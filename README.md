# odoo-custom — image Odoo Startup Pack

Image Odoo personnalisée utilisée par le chart `dna-platform`.

## Contenu

Base **`odoo:19`** + :

| Élément | Chemin dans l'image | Source |
|---|---|---|
| `python-jose[cryptography]` | site-packages | pip (dép. d'`auth_oidc`) |
| `auth_oidc` | `/opt/oca-addons/auth_oidc` | [OCA/server-auth@19.0](https://github.com/OCA/server-auth/tree/19.0/auth_oidc) — vrai client OpenID Connect |

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
