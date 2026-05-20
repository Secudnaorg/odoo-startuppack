# odoo-custom — image Odoo Startup Pack

Image Odoo personnalisée utilisée par le chart `dna-platform`.

## Contenu

Base **`odoo:19`** + :

| Élément | Chemin dans l'image | Source |
|---|---|---|
| `python-jose[cryptography]` | site-packages | pip (dép. d'`auth_oidc`) |
| **Bundle OCA** | `/opt/oca-addons/` (à plat) | dépôts OCA populaires, branche 19.0 |

Les dépôts OCA clonés (branche `19.0`, clone tolérant — un dépôt pas encore
porté sur 19.0 est ignoré) :

`server-auth` (dont `auth_oidc`), `server-tools`, `server-ux`, `server-brand`,
`web` (dont `web_responsive`), `website`, `partner-contact`,
`reporting-engine`, `queue`, `social`, `mail`, `knowledge`, `crm`, `contract`
(dont `subscription_oca`), `account-financial-tools`,
`account-financial-reporting`, `account-invoicing`, `bank-payment`,
`sale-workflow`, `purchase-workflow`, `stock-logistics-warehouse`, `hr`,
`project`, `mis-builder`.

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
