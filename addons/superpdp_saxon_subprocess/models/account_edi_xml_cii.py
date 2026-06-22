# -*- coding: utf-8 -*-
from odoo import models


class AccountEdiXmlCII(models.AbstractModel):
    """Factur-X / CII export: seller legal id = SIREN (not SIRET).

    The SuperPDP (and the PPF) match the seller legal registration identifier
    (SpecifiedLegalOrganization, BT-30) against the SIREN tied to the PDP
    account/session. Native Odoo (`account_edi_ubl_cii`) emits the SIRET
    (14 digits), so the flow is rejected on submission with:

        400 CREATE_ERROR - "company (<SIREN>) of the session does not match the
        invoice seller (<SIRET>)".

    We therefore emit the SIREN (9 digits) as the seller legal id, matching the
    SuperPDP account.

    Conformance note: the schemeID stays "0009" (SIRET) in the native template
    while the value is a SIREN; SuperPDP accepts it. Strictly correct would be
    schemeID "0002" (SIRENE) - to revisit if a validator rejects it.
    """

    _inherit = "account.edi.xml.cii"

    def _export_invoice_vals(self, invoice):
        vals = super()._export_invoice_vals(invoice)
        # A partner that has a SIREN is French by nature, no country check needed.
        company = invoice.company_id
        if getattr(company, "siren", False):
            vals["seller_specified_legal_organization"] = company.siren
        return vals
