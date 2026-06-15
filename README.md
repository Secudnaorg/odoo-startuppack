# odoo-custom — image Odoo Startup Pack

Image Odoo personnalisée utilisée par le chart `dna-platform`.

## Contenu

Base **`odoo:18`** + :

| Élément | Chemin dans l'image | Source |
|---|---|---|
| `python-jose[cryptography]` | site-packages | pip (dép. d'`auth_oidc`) |
| `pyfrctc`, `saxonche`, `factur-x`, `packaging` | site-packages | pip (e-facture PDP SuperPDP) |
| **Bundle OCA** | `/opt/oca-addons/` (à plat) | dépôts OCA populaires, branche 18.0 |
| **`fr-einvoicing`** (Akretion) | `/opt/oca-addons/` | `akretion/fr-einvoicing` 18.0 (connecteur PDP `l10n_fr_einvoicing`) |
| **`superpdp_saxon_subprocess`** | `/opt/oca-addons/` | `addons/` (correctif réception e-facture) |

Les dépôts OCA clonés (branche `18.0`, clone tolérant — un dépôt pas encore
porté sur 18.0 est ignoré) :

`server-auth` (dont `auth_oidc`), `server-tools`, `server-ux`, `server-brand`,
`web` (dont `web_responsive`), `website`, `partner-contact`,
`reporting-engine`, `queue`, `social`, `mail`, `knowledge`, `crm`, `contract`
(dont **`subscription_oca`** = ABONNEMENTS), `account-financial-tools`,
`account-financial-reporting`, `account-invoicing`, `bank-payment`,
`sale-workflow`, `purchase-workflow`, `stock-logistics-warehouse`, `hr`,
`project`, `mis-builder`, **`l10n-france`**, **`edi`**, **`edi-framework`**
(= FACTURATION ÉLECTRONIQUE FR / PDP : Factur-X, Chorus Pro, cadre EDI
`account_edi`), **`community-data-files`** (`base_unece`/`account_tax_unece` —
requis par l'import de factures).

### E-facturation PDP (SuperPDP / AFNOR) — envoi & réception

En plus du bundle OCA, l'image embarque le connecteur **Akretion
`fr-einvoicing`** (`l10n_fr_einvoicing`, `l10n_fr_einvoicing_import`) et le
correctif maison **`superpdp_saxon_subprocess`** :

- **Saxon en sous-process** — `saxonche` (Saxon-C/GraalVM) est fork/thread-unsafe
  et plante les workers Odoo (`graal_create_isolate`) ; le module exécute la
  validation schematron dans un `python3` neuf. Couvre `pyfrctc` et `factur-x`.
- **Normalisation UBL** — réécrit l'UBL sans préfixes (`cbc:`/`cac:`) émis par le
  PDP avant le parseur OCA `account_invoice_import_ubl`.

Détails complets, schémas de flux et limites sandbox : **[`docs/SUPERPDP.md`](docs/SUPERPDP.md)**.
Bugs amont remontés : `akretion/pyfrctc#3`, `akretion/fr-einvoicing#9`.

Couvre les 10 dépôts de la [liste « must-have OCA »](https://www.odoo-community.org/list-of-must-have-oca-modules)
(`web_responsive`, `mail_debrand`, `queue_job`, `report_xlsx`, …).

⚠️ Les modules sont **disponibles, pas installés** — un admin les active
depuis Odoo > Apps. Certains modules réclament des paquets Python
supplémentaires (`external_dependencies`) à ajouter au besoin.

## Build

Automatique via GitHub Actions (`.github/workflows/build-image.yml`) à chaque
push sur `main` — poussé sur **Harbor**, comme l'image `onboarding_platform` :

```
public-harbor.gottaphish.com/startuppack/odoo-custom:latest
public-harbor.gottaphish.com/startuppack/odoo-custom:<sha7>
```

Requiert les secrets `HARBOR_USERNAME` / `HARBOR_PASSWORD` (secrets
d'organisation, ou à ajouter au repo).

## Utilisation côté chart

Dans `dna-platform`, pointer `odoo.image` sur
`public-harbor.gottaphish.com/startuppack/odoo-custom:latest` et ajouter
`/opt/oca-addons` à `--addons-path`. Installer `auth_oidc` via `-i`.

Le pull est couvert par l'`imagePullSecret` Harbor existant
(`harbor-startuppack-pull`) déjà présent dans les namespaces tenants.
