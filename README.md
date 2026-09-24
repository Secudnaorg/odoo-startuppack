# odoo-custom — Startup Pack Odoo image

Custom Odoo image used by the `dna-platform` chart.

## Contents

Base **`docker.io/odoo:18`** plus:

| Item | Path in the image | Source |
|---|---|---|
| `python-jose[cryptography]` | site-packages | pip (dependency of `auth_oidc`) |
| `pyfrctc`, `factur-x`, `packaging`, `requests_oauthlib` | site-packages | pip (FR e-invoicing via the SuperPDP PDP) |
| **OCA bundle** | `/opt/oca-addons/` (flat) | OCA repos, **pinned to a commit** |
| **`fr-einvoicing`** (Akretion) | `/opt/oca-addons/` | `akretion/fr-einvoicing`, pinned (PDP connector `l10n_fr_einvoicing`) |
| **Local Startup Pack addons** | `/opt/oca-addons/` | `addons/` (see below) |

> **Note** — Saxon is **no longer** installed in-process (`saxonche` was dropped).
> Schematron validation now runs in a **Saxon Server sidecar** reached over HTTP
> (see [E-invoicing](#e-invoicing-pdp--superpdp--afnor) below).

### Pinned OCA / Akretion repositories

Every repo is **pinned to an exact commit** (coherent snapshot, 2026-09-24) rather
than tracking the floating `18.0` branch. This gives reproducible builds and avoids
the inter-repo drift that used to break `l10n_fr_einvoicing_import`. To upgrade,
bump the commit SHAs in the `Dockerfile` clone loop.

`server-auth` (incl. `auth_oidc`), `server-tools`, `server-ux`, `server-brand`,
`web` (incl. `web_responsive`), `website`, `partner-contact`, `reporting-engine`,
`queue`, `social`, `mail`, `knowledge`, `crm`, `contract` (incl.
**`subscription_oca`** = SUBSCRIPTIONS), `account-financial-tools`,
`account-financial-reporting`, `account-invoicing`, `bank-payment`,
`sale-workflow`, `purchase-workflow`, `stock-logistics-warehouse`, `hr`, `project`,
`mis-builder`, **`l10n-france`**, **`edi`**, **`edi-framework`** (= FR ELECTRONIC
INVOICING / PDP: Factur-X, Chorus Pro, the `account_edi` EDI framework),
**`community-data-files`** (`base_unece` / `account_tax_unece`, required by the
invoice import).

### Local Startup Pack addons (`addons/`)

Copied into `/opt/oca-addons/` (same `--addons-path` entry). All of them are
**vendored directly in this repo** — there is no git submodule, so the build works
from any fork/CI without submodule init or SSH keys.

| Module | Role |
|---|---|
| `auth_oidc` | Patched OCA `auth_oidc` (OIDC login). |
| `sp_auth_oidc_roles` | Maps Keycloak roles (from the OIDC token) to Odoo groups **at login**, plus IdP-initiated logout (RP-initiated + OIDC back-channel). Source of truth = the token (no cron, no SQL trigger). Install/upgrade from the chart via `-i/-u sp_auth_oidc_roles`. |
| `sp_facturx_pdf_fix` | Generates valid Factur-X PDF/A-3 from Odoo report streams. |
| `superpdp_saxon_subprocess` | Normalises PDP UBL (strips the `cbc:` / `cac:` prefixes) before the OCA `account_invoice_import_ubl` parser. Required for e-invoice **reception**. |

### E-invoicing (PDP / SuperPDP / AFNOR) — send & receive

On top of the OCA bundle, the image ships the Akretion **`fr-einvoicing`**
connector (`l10n_fr_einvoicing`, `l10n_fr_einvoicing_import`) and the in-house
`superpdp_saxon_subprocess` normaliser.

Schematron validation (`pyfrctc`, `factur-x`) runs against an **external Saxon
Server** rather than the in-process `saxonche` (Saxon-C / GraalVM), which is
fork/thread-unsafe and crashed the Odoo workers (`graal_create_isolate`). The
Saxon Server runs as a **sidecar container** next to Odoo and is reached over HTTP
— it is wired in the SRE deployment (`sre/hetzner/infra/internal/odoo18/odoo.yml`),
not in this image.

Full details, flow diagrams and sandbox limits: **[`docs/SUPERPDP.md`](docs/SUPERPDP.md)**.
Upstream bugs reported: `akretion/pyfrctc#3`, `akretion/fr-einvoicing#9`.

Covers the 10 repos of the [OCA "must-have" list](https://www.odoo-community.org/list-of-must-have-oca-modules)
(`web_responsive`, `mail_debrand`, `queue_job`, `report_xlsx`, …).

> ⚠️ Modules are **available, not installed** — an admin enables them from
> Odoo > Apps. Some modules require extra Python packages (`external_dependencies`);
> add them as needed.

## Build

**GitHub Actions** (`.github/workflows/build-image.yml`) on every push to `main`,
pushed to **Harbor**:

```
public-harbor.gottaphish.com/startuppack/odoo-custom:latest
public-harbor.gottaphish.com/startuppack/odoo-custom:<sha7>
```

Requires the `HARBOR_USERNAME` / `HARBOR_PASSWORD` secrets (org secrets, or added
to the repo).

The image is also built by an **internal Jenkins pipeline** from the
`Secudnaorg/odoo-startuppack` fork (podman). Two things make this fork-based build
work out of the box: the base image is **fully qualified** (`docker.io/odoo:18`,
because podman does not assume `docker.io` for short names), and every local addon
is **vendored** (no submodule to init).

## Chart usage

In `dna-platform`, point `odoo.image` at
`public-harbor.gottaphish.com/startuppack/odoo-custom:latest`, add
`/opt/oca-addons` to `--addons-path`, and install `auth_oidc` + `sp_auth_oidc_roles`
via `-i`. For e-invoicing reception/validation, the **Saxon Server sidecar** must be
present (see the SRE deployment).

The pull is covered by the existing Harbor `imagePullSecret`
(`harbor-startuppack-pull`) already present in tenant namespaces.
