# Image Odoo personnalisée Startup Pack.
# Base Odoo 18 + SSO OpenID Connect (OCA auth_oidc) + un bundle des
# dépôts OCA les plus populaires, dont les abonnements (subscription_oca,
# dépôt `contract`) et la facturation électronique FR / PDP (Factur-X,
# Chorus Pro, EDI — dépôts `l10n-france`, `edi`, `edi-framework`).
# Construite par GitHub Actions.
FROM odoo:18

USER root

# Dépendances Python :
#  - python-jose : module OCA auth_oidc (validation des JWT OIDC)
#  - pyfrctc / saxonche / factur-x : e-facturation FR via PDP SuperPDP
#    (connecteur AFNOR `l10n_fr_einvoicing`, validation schematron, Factur-X)
#  - packaging : requis par Odoo pour parser les dépendances externes des modules
RUN pip3 install --no-cache-dir --break-system-packages \
    "python-jose[cryptography]" \
    packaging \
    "pyfrctc>=0.10" \
    saxonche \
    "factur-x" \
    requests_oauthlib

# Tous les modules OCA sont aplatis dans /opt/oca-addons (un seul chemin à
# ajouter à --addons-path côté chart). Les modules ne sont PAS installés :
# ils sont seulement disponibles — un admin les active depuis Odoo > Apps.
RUN mkdir -p /opt/oca-addons

# Dépôts OCA populaires, branche 18.0. Clone TOLÉRANT : un dépôt pas encore
# porté sur 18.0 est simplement ignoré.
#  - `contract` fournit subscription_oca (ABONNEMENTS).
#  - `l10n-france`, `edi`, `edi-framework` fournissent la FACTURATION
#    ÉLECTRONIQUE FR / PDP (Factur-X, Chorus Pro, cadre EDI account_edi).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends git ca-certificates; \
    for repo in \
        server-auth server-tools server-ux server-brand web website \
        partner-contact reporting-engine queue social mail knowledge \
        crm contract \
        account-financial-tools account-financial-reporting account-invoicing \
        bank-payment sale-workflow purchase-workflow \
        stock-logistics-warehouse hr project mis-builder \
        l10n-france edi edi-framework community-data-files ; do \
      if git clone --depth 1 --branch 18.0 "https://github.com/OCA/$repo.git" "/tmp/oca-$repo" 2>/dev/null; then \
        cp -rn /tmp/oca-$repo/*/ /opt/oca-addons/ 2>/dev/null || true; \
        rm -rf "/tmp/oca-$repo"; \
        echo "OCA $repo : cloné (18.0)"; \
      else \
        echo "OCA $repo : pas de branche 18.0 — ignoré"; \
      fi; \
    done; \
    git clone --depth 1 --branch 18.0 https://github.com/akretion/fr-einvoicing.git /tmp/akretion-fr-einvoicing \
      && cp -rn /tmp/akretion-fr-einvoicing/*/ /opt/oca-addons/ 2>/dev/null || true; \
    rm -rf /tmp/akretion-fr-einvoicing; \
    rm -rf /opt/oca-addons/setup /opt/oca-addons/.github; \
    apt-get purge -y git; apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/* /tmp/oca-*

# Addons maison Startup Pack (déposés dans le même /opt/oca-addons déjà sur le
# --addons-path).
#  - `sp_auth_oidc_roles` mappe les rôles Keycloak du token OIDC vers les groupes
#    Odoo AU LOGIN — installé/maj côté chart via `-i/-u sp_auth_oidc_roles`.
#  - `superpdp_saxon_subprocess` exécute la validation Saxon (saxonche) en
#    sous-process (sinon crash GraalVM fork/thread-unsafe dans les workers Odoo)
#    et normalise l'UBL sans préfixes du PDP avant l'import OCA. Requis pour la
#    RÉCEPTION e-facture. Voir docs/SUPERPDP.md.
COPY addons/ /opt/oca-addons/

# /opt/oca-addons à ajouter à --addons-path côté chart (en plus de
# /mnt/extra-addons). Le module auth_oidc en fait partie (dépôt server-auth).
RUN chown -R odoo:odoo /opt/oca-addons

USER odoo
