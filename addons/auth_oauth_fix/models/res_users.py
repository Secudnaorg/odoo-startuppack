import base64
import json
import logging
import traceback
import requests as http_requests
from odoo import models

_logger = logging.getLogger(__name__)

# Keycloak role name  →  list of Odoo group XML IDs to grant.
# `base.group_user` is the "Internal User" group — required to flip share=False
# and unlock the back-office. Without it the SSO user is provisioned as a portal
# user and lands on /web/login_successful with no menus.
#
# Two key sets coexist here on purpose:
#  - Per-client roles on the `odoo` Keycloak client (primary, set by the
#    "client-roles-userinfo" protocol mapper, claim resource_access.odoo.roles).
#    Names mirror Odoo personas; users may carry several to compose groups.
#  - Realm roles (legacy fallback) so users provisioned before the per-client
#    taxonomy still resolve to a sensible group set.
# env.ref() raises if a module isn't installed; _apply_role_mapping catches
# that silently per-XML-ID, so listing extra mappings here is safe.
ROLE_MAP = {
    # ── Odoo client roles (primary) ──────────────────────────────────────────
    "internal-user":      ["base.group_user"],
    "system-admin":       ["base.group_user", "base.group_system", "base.group_erp_manager"],
    "sales-manager":      ["base.group_user", "sales_team.group_sale_manager"],
    "sales-user":         ["base.group_user", "sales_team.group_sale_salesman"],
    "hr-manager":         ["base.group_user", "hr.group_hr_manager"],
    "hr-user":            ["base.group_user", "hr.group_hr_user"],
    "accounting-manager": ["base.group_user", "account.group_account_manager"],
    "accounting-user":    ["base.group_user", "account.group_account_user"],
    "website-designer":   ["base.group_user", "website.group_website_designer"],

    # ── Realm roles (legacy fallback) ───────────────────────────────────────
    "commercial":            ["base.group_user", "sales_team.group_sale_manager"],
    "technical":             ["base.group_user", "base.group_system"],
    "marketing":             ["base.group_user", "website.group_website_designer"],
    "rh":                    ["base.group_user", "hr.group_hr_manager"],
    "stagiaire-technical":   ["base.group_user"],
    "stagiaire-commercial":  ["base.group_user"],
    "stagiaire-marketing":   ["base.group_user"],
    "stagiaire-rh":          ["base.group_user"],
}


class ResUsers(models.Model):
    _inherit = "res.users"

    def _auth_oauth_validate(self, provider, access_token):
        # Stock auth_oauth calls validation_endpoint with the access token as a
        # query param (?access_token=...); Keycloak's userinfo endpoint only
        # accepts Authorization: Bearer. We override to send the proper header.
        p = self.env["auth.oauth.provider"].browse(provider)
        resp = http_requests.get(
            p.validation_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        validation = resp.json()
        if validation.get("error"):
            raise Exception(validation["error"])
        if p.data_endpoint:
            data = http_requests.get(
                p.data_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            ).json()
            validation.update(data)
        validation["user_id"] = validation.get("sub", validation.get("user_id", ""))
        return validation

    def _auth_oauth_signin(self, provider, validation, params):
        login = super()._auth_oauth_signin(provider, validation, params)
        # The upstream auth_oauth controller catches AttributeError and reports
        # "auth_signup not installed" — masking real failures here. Log the real
        # cause so future debugging doesn't require deep grepping.
        try:
            user = self.sudo().search([("login", "=", login)], limit=1)
            if user:
                roles = self._extract_keycloak_roles(
                    validation, params.get("access_token", "")
                )
                self._apply_role_mapping(user, roles)
        except Exception:
            _logger.error(
                "auth_oauth_fix: role mapping for %s failed:\n%s",
                login,
                traceback.format_exc(),
            )
            raise
        return login

    def _extract_keycloak_roles(self, validation, access_token=""):
        """Collect roles from userinfo claims and/or JWT access token payload."""
        roles = set()
        # From userinfo response (requires Keycloak mapper on the client scope)
        for r in validation.get("roles", []):
            roles.add(r)
        for r in validation.get("realm_access", {}).get("roles", []):
            roles.add(r)
        for client_data in validation.get("resource_access", {}).values():
            for r in client_data.get("roles", []):
                roles.add(r)
        # Fallback: decode JWT access token (no signature verification)
        if access_token:
            try:
                payload_b64 = access_token.split(".")[1]
                payload_b64 += "=" * (-len(payload_b64) % 4)
                payload = json.loads(base64.b64decode(payload_b64))
                for r in payload.get("realm_access", {}).get("roles", []):
                    roles.add(r)
                for client_data in payload.get("resource_access", {}).values():
                    for r in client_data.get("roles", []):
                        roles.add(r)
            except Exception:
                pass
        return roles

    def _apply_role_mapping(self, user, roles):
        """Assign Odoo groups that correspond to the user's Keycloak roles.

        Odoo 19 enforces mutually-exclusive "user-type" groups via
        res.groups._get_user_type_groups() (Portal / Public / Internal User).
        We must remove any conflicting user-type group before adding the new
        one, otherwise res.users._check_disjoint_groups raises ValidationError.
        """
        user_type_groups = self.env["res.groups"].sudo()._get_user_type_groups()
        wanted_group_ids = []
        for kc_role, xml_ids in ROLE_MAP.items():
            if kc_role not in roles:
                continue
            for xml_id in xml_ids:
                try:
                    group = self.env.ref(xml_id)
                except Exception:
                    continue
                wanted_group_ids.append(group.id)

        if not wanted_group_ids:
            return

        wanted = self.env["res.groups"].sudo().browse(wanted_group_ids)
        # If any wanted group is a user-type group (or implies one), drop
        # the other user-type groups currently assigned.
        wanted_user_type = wanted.all_implied_ids & user_type_groups
        if wanted_user_type:
            to_remove = (user.group_ids & user_type_groups) - wanted_user_type
            commands = [(3, g.id) for g in to_remove]
        else:
            commands = []
        for gid in wanted_group_ids:
            commands.append((4, gid))
        user.sudo().write({"group_ids": commands})
