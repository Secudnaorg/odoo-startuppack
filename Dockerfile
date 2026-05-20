# Image Odoo personnalisée Startup Pack.
# Base Odoo 19 + SSO OpenID Connect (OCA auth_oidc) + addon maison de
# mapping des rôles Keycloak. Construite par GitHub Actions.
FROM odoo:19

USER root

# Dépendance Python du module OCA auth_oidc (validation des JWT OIDC).
RUN pip3 install --no-cache-dir --break-system-packages "python-jose[cryptography]"

# Addons additionnels placés hors de /mnt/extra-addons : ce chemin est monté
# en volume par le chart Helm et masquerait des addons baked-in.
RUN mkdir -p /opt/oca-addons

# OCA auth_oidc — vrai client OpenID Connect (dépôt server-auth, branche 19.0).
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends git ca-certificates; \
    git clone --depth 1 --branch 19.0 https://github.com/OCA/server-auth.git /tmp/server-auth; \
    cp -r /tmp/server-auth/auth_oidc /opt/oca-addons/auth_oidc; \
    rm -rf /tmp/server-auth; \
    apt-get purge -y git; apt-get autoremove -y; rm -rf /var/lib/apt/lists/*

# Addon maison : mapping rôles Keycloak -> groupes Odoo (+ fix historique).
COPY addons/ /opt/oca-addons/

# Les addons baked-in sont dans /opt/oca-addons : à ajouter à --addons-path
# côté chart (en plus de /mnt/extra-addons).
RUN chown -R odoo:odoo /opt/oca-addons

USER odoo
