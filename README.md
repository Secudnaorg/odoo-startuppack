# odoo-custom — image Odoo Startup Pack

Image Odoo personnalisée utilisée par le chart `dna-platform`.

## Contenu

Base **`odoo:19`** + :

| Élément | Chemin dans l'image | Source |
|---|---|---|
| `python-jose[cryptography]` | site-packages | pip (dép. d'`auth_oidc`) |
| `auth_oidc` | `/opt/oca-addons/auth_oidc` | [OCA/server-auth@19.0](https://github.com/OCA/server-auth/tree/19.0/auth_oidc) — vrai client OpenID Connect |
| `auth_oauth_fix` | `/opt/oca-addons/auth_oauth_fix` | addon maison — mapping rôles Keycloak → groupes Odoo |

## Build

Automatique via GitHub Actions (`.github/workflows/build-image.yml`) à chaque push sur `main` ou tag `v*` :

```
ghcr.io/startuppack/odoo-custom:latest
ghcr.io/startuppack/odoo-custom:main
ghcr.io/startuppack/odoo-custom:<sha>
ghcr.io/startuppack/odoo-custom:<version>   # sur tag vX.Y.Z
```

## Utilisation côté chart

Dans `dna-platform`, pointer `odoo.image` sur `ghcr.io/startuppack/odoo-custom:latest`
et ajouter `/opt/oca-addons` à `--addons-path`. Installer `auth_oidc` via `-i`
(`auth_oauth_fix` a `auto_install: true`).

⚠️ Le package GHCR doit être **public**, ou un `imagePullSecret` GHCR doit être
ajouté aux namespaces des tenants.
