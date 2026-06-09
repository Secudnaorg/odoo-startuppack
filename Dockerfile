# Image Odoo personnalisée Startup Pack.
# Base Odoo 19 + SSO OpenID Connect (OCA auth_oidc) + un bundle des
# dépôts OCA les plus populaires. Construite par GitHub Actions.
FROM odoo:19

USER root

# Dépendance Python du module OCA auth_oidc (validation des JWT OIDC).
RUN pip3 install --no-cache-dir --break-system-packages "python-jose[cryptography]"

# Tous les modules OCA sont aplatis dans /opt/oca-addons (un seul chemin à
# ajouter à --addons-path côté chart). Les modules ne sont PAS installés :
# ils sont seulement disponibles — un admin les active depuis Odoo > Apps.
RUN mkdir -p /opt/oca-addons

# Dépôts OCA populaires, branche 19.0. Clone TOLÉRANT : un dépôt pas encore
# porté sur 19.0 est simplement ignoré (le portage OCA 19.0 est en cours).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends git ca-certificates; \
    for repo in \
        server-auth server-tools server-ux server-brand web website \
        partner-contact reporting-engine queue social mail knowledge \
        crm contract \
        account-financial-tools account-financial-reporting account-invoicing \
        bank-payment sale-workflow purchase-workflow \
        stock-logistics-warehouse hr project mis-builder ; do \
      if git clone --depth 1 --branch 19.0 "https://github.com/OCA/$repo.git" "/tmp/oca-$repo" 2>/dev/null; then \
        cp -rn /tmp/oca-$repo/*/ /opt/oca-addons/ 2>/dev/null || true; \
        rm -rf "/tmp/oca-$repo"; \
        echo "OCA $repo : cloné (19.0)"; \
      else \
        echo "OCA $repo : pas de branche 19.0 — ignoré"; \
      fi; \
    done; \
    rm -rf /opt/oca-addons/setup /opt/oca-addons/.github; \
    apt-get purge -y git; apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/* /tmp/oca-*

# Addons maison Startup Pack (déposés dans le même /opt/oca-addons déjà sur le
# --addons-path). `sp_auth_oidc_roles` mappe les rôles Keycloak du token OIDC
# vers les groupes Odoo AU LOGIN (admin/interne) — installé/maj côté chart via
# `-i/-u sp_auth_oidc_roles`.
COPY addons/ /opt/oca-addons/

# /opt/oca-addons à ajouter à --addons-path côté chart (en plus de
# /mnt/extra-addons). Le module auth_oidc en fait partie (dépôt server-auth).
RUN chown -R odoo:odoo /opt/oca-addons

USER odoo
