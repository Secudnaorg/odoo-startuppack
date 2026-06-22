# -*- coding: utf-8 -*-
from odoo import models


class ResPartner(models.Model):
    """French e-invoicing electronic address = scheme 0225 (FRCTC) + SIREN.

    The SuperPDP submission pre-check looks up the recipient by its e-invoicing
    electronic address. In France this is the SIREN under scheme 0225
    ("France FRCTC Electronic Address"):

        <ram:URIUniversalCommunication>
            <ram:URIID schemeID="0225">843228636</ram:URIID>
        </ram:URIUniversalCommunication>

    Native Odoo (`account_edi_ubl_cii`) defaults peppol_eas to 0009 (SIRET) or
    9957 (VAT), hence the rejection:
        400 CREATE_ERROR - "pre-check: receiver address does not exist in
        peppol directory".

    We force, for any partner that has a SIREN (i.e. French), peppol_eas=0225
    and peppol_endpoint=<SIREN>.

    Note: these fields are computed-stored (recomputed when country/VAT/registry
    change); this override keeps the correct value across recomputes and for new
    partners.
    """

    _inherit = "res.partner"

    def _compute_peppol_eas(self):
        # A partner that has a SIREN is French by nature, no country check needed.
        super()._compute_peppol_eas()
        for partner in self:
            if getattr(partner, "siren", False):
                partner.peppol_eas = "0225"

    def _compute_peppol_endpoint(self):
        super()._compute_peppol_endpoint()
        for partner in self:
            if partner.peppol_eas == "0225" and getattr(partner, "siren", False):
                partner.peppol_endpoint = partner.siren
