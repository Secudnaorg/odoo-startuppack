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
    "pyfrctc>=0.22" \
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
# Dépôts OCA + akretion ÉPINGLÉS à un commit (snapshot cohérent 2026-09-24) :
# reproductibilité + évite la dérive inter-dépôts qui cassait l10n_fr_einvoicing_import.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends git ca-certificates \
        ghostscript fonts-dejavu fonts-liberation fontconfig; \
    for spec in \
      "https://github.com/OCA/server-auth.git|880317035e338f45ccc76e43c000ed2df62d306a" \
      "https://github.com/OCA/server-tools.git|f2de15fa429cc555e6367ed53da063f184b2bc5c" \
      "https://github.com/OCA/server-ux.git|5a67ed407c07160ee1b4fc74b8d2e6eb5507fa2b" \
      "https://github.com/OCA/server-brand.git|c296e5a6284a7bf7f6fe8f941685cbf31f89375a" \
      "https://github.com/OCA/web.git|f9eb80e0da0dce4d67edb1237293364237f96a95" \
      "https://github.com/OCA/website.git|7e44dc36e688fea2f8971051dc4170d1e0951328" \
      "https://github.com/OCA/partner-contact.git|78a933a8702a55ee2880d12bbe0746a150d76377" \
      "https://github.com/OCA/reporting-engine.git|7a156caae6558276408854ef26b729331e974361" \
      "https://github.com/OCA/queue.git|d3ce20aa625fc4ee4a9984bf0b4dd6196fcfc0ed" \
      "https://github.com/OCA/social.git|eeee83eb0bf79b74c0c4ab6f6fdb57806c8b49e8" \
      "https://github.com/OCA/mail.git|81977d4e3919b7e87f229f4570cdbc4dee9ebe84" \
      "https://github.com/OCA/knowledge.git|c6ea66af11876215b1aaac68975fa6cbcd586e57" \
      "https://github.com/OCA/crm.git|07c248596b687fb71e74fefe1fa2e100068ac39d" \
      "https://github.com/OCA/contract.git|14b3b89b55f481427fd08bf350ef68d320e8903a" \
      "https://github.com/OCA/account-financial-tools.git|e4c1b86aa0a61d9f484c1a7e9830a63f5e6a2233" \
      "https://github.com/OCA/account-financial-reporting.git|9291961e21c9af317f4972dd90e877730759a39f" \
      "https://github.com/OCA/account-invoicing.git|4a634ffce03546de8220e8dcf57b9fc159bf0b67" \
      "https://github.com/OCA/bank-payment.git|57975b134737b71eb9762f24746422fe828133a5" \
      "https://github.com/OCA/sale-workflow.git|a86d8041599b49efb2fc35e36a3905ebcc1ded0f" \
      "https://github.com/OCA/purchase-workflow.git|80ef750ffe0f49addf3289a50afc7618a60782f4" \
      "https://github.com/OCA/stock-logistics-warehouse.git|53d75c6399df1a72611f1fa1a162e5ce9da75d18" \
      "https://github.com/OCA/hr.git|33ad2e23b682d6abcbbdc98ac4b6807fa2e180fa" \
      "https://github.com/OCA/project.git|2780d8a3041a97966cd808fd253a67aea66bc40b" \
      "https://github.com/OCA/mis-builder.git|4f9eef0954af7dfdb1d13451f4d860602b074cda" \
      "https://github.com/OCA/l10n-france.git|24a69693f421503f8798ada6af0c046cb3f054d0" \
      "https://github.com/OCA/edi.git|a43bfc5f68d4f9d307337ec64e9a4840639a7c0c" \
      "https://github.com/OCA/edi-framework.git|9f8ad18bfcc8e3b6030ef7aecad51b5115233780" \
      "https://github.com/OCA/community-data-files.git|d32b2cc1ca50bfb304cb4c6cf25f99977383426d" \
      "https://github.com/akretion/fr-einvoicing.git|7d841d914bcedebfc17cabae936a8113fa2785d9" \
    ; do \
      url="${spec%%|*}"; sha="${spec##*|}"; name="$(basename "$url" .git)"; \
      mkdir -p "/tmp/oca-$name"; \
      git -C "/tmp/oca-$name" init -q; \
      git -C "/tmp/oca-$name" remote add origin "$url"; \
      git -C "/tmp/oca-$name" fetch --depth 1 origin "$sha"; \
      git -C "/tmp/oca-$name" checkout -q FETCH_HEAD; \
      cp -rn /tmp/oca-$name/*/ /opt/oca-addons/ 2>/dev/null || true; \
      rm -rf "/tmp/oca-$name"; \
    done; \
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

# Cache fontconfig inscriptible. L'utilisateur odoo a HOME=/ (non inscriptible)
# et aucun XDG_CACHE_HOME -> wkhtmltopdf/ghostscript échouent avec
# "Fontconfig error: No writable cache directories", ce qui casse la génération
# du PDF/A-3 Factur-X (le PDP rejette alors un PDF brut sans factur-x.xml).
# /var/lib/odoo est inscriptible par odoo (uid 101) ; fontconfig y crée son cache.
ENV XDG_CACHE_HOME=/var/lib/odoo/.cache

USER odoo
