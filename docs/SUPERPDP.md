# SuperPDP / AFNOR e-invoicing on Odoo 18

How we set up **sending and receiving** electronic invoices through the certified
platform (PA/PDP) **SuperPDP** (`api.superpdp.tech`), as part of the French
e-invoicing reform.

## 1. Components

| Item | Detail |
|---|---|
| Platform | SuperPDP — base `https://api.superpdp.tech` |
| OAuth token | `POST /oauth2/token` (`client_credentials` grant), access token ~30 min |
| "Simple" API | `/v1.beta/...` (send/receive, test-invoice generation) |
| AFNOR API | `/afnor-flow/v1/...`, `/afnor-directory/v1/...` (used by the Odoo module) |
| Odoo module | `l10n_fr_einvoicing` (+ `l10n_fr_einvoicing_import` for receiving) — Akretion |
| Python libs | `pyfrctc` (AFNOR client), `saxonche` (schematron validation) |
| Vendor docs | `https://api.superpdp.tech/internal/articles/{N}/html` (N = 1,2,3…) |
| Example | `https://raw.githubusercontent.com/superpdp/examples/refs/heads/main/quick_start.js` |

### Sandbox accounts
The sandbox provides two fictitious companies that invoice each other:
**Burger Queen** (number `000000002`) and **Tricatel** (number `000000001`).
Their identifier uses `number_scheme = "sandbox"` (it is **not** a real SIREN):
```
GET /v1.beta/companies/me  ->  {"number_scheme":"sandbox","number":"000000001","formal_name":"Tricatel",...}
```

## 2. Configuration

### Dependencies added to the image (Dockerfile)
- Pip: `packaging` (needed to parse external-dependency version specs).
- Extra OCA repos cloned: **server-tools** (`base_view_inheritance_extension`),
  **community-data-files** (`base_unece`, `account_tax_unece`, `uom_unece`),
  added to `addons_path`.
- Local module `superpdp_saxon_subprocess` (see §5).

### odoo.conf / k8s Secret
- `running_env = test` → SuperPDP uses the sandbox scheme.
- Credentials stored in k8s Secret `superpdp-demo` (ns `odoo18`) and mirrored on the
  company: `fr_ctc_accredited_platform=superpdp`, `fr_ctc_auth_method=client_credentials`,
  `fr_ctc_client_id`, `fr_ctc_client_secret`.

### Directory (routing)
A French billing address = Peppol scheme **`0225`** + **SIREN** (or `SIREN_SIRET`).
Check whether a recipient is reachable:
```
pyfrctc.get_directory_siren(session, "950929885")   # -> dict if present in the directory
```

## 3. Sending an invoice

### Via the simple API (works in sandbox; the platform handles the "sandbox" identity)
```
token = POST /oauth2/token (client_credentials)
xml   = GET  /v1.beta/invoices/generate_test_invoice?format=ubl   (Bearer token)
POST  /v1.beta/invoices  (Bearer token, body = xml)   ->  200, {"id":...,"status":"Téléversée"}
```

### Via the Odoo module (target for production with a real SIREN)
Post a customer invoice: the `account.move._post` hook creates an
`fr.einvoicing.flow` then sends it (`fr_ctc_send_invoice_immediately_button` or the
"send outgoing flows" cron). The company must be present in the directory
(`fr_directory_entity_type='private'`, valid SIREN). In **sandbox**, the identity
`000000001` is not a valid SIREN, so use the simple API above.

## 4. Receiving an invoice

1. A sending platform (e.g. Burger Queen) issues an invoice addressed to our SIREN.
2. Odoo cron "FR eInvoicing: import incoming flows" → `fr.einvoicing.flow._in_cron()`
   calls `pyfrctc.search_flows(session, updated_after, ["in"], [...])`, downloads the
   incoming flows and stores them as `fr.einvoicing.flow` (direction `in`).
3. The module turns the invoice (UBL/CII) into a **draft vendor bill** via
   `account_invoice_import` (lxml parsing), and processes lifecycle flows (CDAR) —
   this is where Saxon schematron validation kicks in (see §5).

Check reception via the API:
```
GET /v1.beta/invoices?order=desc   ->  entries with "direction":"in"
GET /v1.beta/invoices/{id}         ->  parsed EN16931 content
```

## 5. Gotcha: saxonche (Saxon-C / GraalVM) is fork/thread-unsafe

`l10n_fr_einvoicing` (via `pyfrctc._cdar_check_schematron`) validates the XML with
**saxonche**, which is built with GraalVM. A GraalVM *isolate* is bound to the
thread/process that created it: it **survives neither a secondary thread nor a
`fork()`**.

Odoo never runs code in the process main thread:
- `workers = 0` (threaded) → crons/requests run in threads → **crash**
  (`graal_create_isolate`, *Failed to enter the specified IsolateThread context*)
  that **kills the pod**;
- `workers > 0` (prefork) → forked processes → **crash** of the worker (the pod
  survives but the import fails), and requires the longpolling config.

`python3 -c "from saxonche import PySaxonProcessor; PySaxonProcessor()"` works
(fresh process, main thread) — that is the key to the fix.

### Fix: module `superpdp_saxon_subprocess`
Monkeypatches `pyfrctc._cdar_check_schematron` to run the Saxon XSLT 3.0
transformation in a **fresh `python3` subprocess** (`subprocess.run` = fork+exec,
so no inherited isolate). The rest of the logic (SVRL parsing, error raising) is
kept. Install the module; it activates on load.

> Until this fix is loaded, keep the e-invoicing crons
> ("FR eInvoicing: import/send") **disabled** to avoid a pod crash-loop.

## 6. Handy commands (odoo shell)
```python
company = env.ref('base.main_company')
session = company._fr_ctc_get_session()                  # token via the module
from pyfrctc import pyfrctc
pyfrctc.healthcheck(session, type="directory")           # True if OK
pyfrctc.get_directory_siren(session, "950929885")        # recipient reachable?
flows, result = company.fr_ctc_run_import_log('manual')  # import incoming flows
```
