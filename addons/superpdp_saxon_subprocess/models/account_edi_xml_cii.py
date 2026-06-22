# -*- coding: utf-8 -*-
from odoo import models


class AccountEdiXmlCII(models.AbstractModel):
    """Émission Factur-X / CII : identifiant légal vendeur = SIREN (pas SIRET).

    Le SuperPDP (et le PPF) rapprochent l'identifiant légal du vendeur
    (SpecifiedLegalOrganization, BT-30) du **SIREN** rattaché au compte/à la
    session PDP. Odoo natif (`account_edi_ubl_cii`) y met le **SIRET**
    (14 chiffres). Résultat : le flux est rejeté à l'émission avec

        400 CREATE_ERROR - « L'entreprise (<SIREN>) liée à cette session ne
        correspond pas au vendeur de la facture (<SIRET>) ».

    Pour les sociétés françaises, on émet donc le SIREN (9 chiffres) comme
    identifiant légal vendeur, ce qui correspond au compte SuperPDP.

    NB conformité : le schemeID reste « 0009 » (SIRET) côté gabarit natif alors
    que la valeur est un SIREN ; SuperPDP l'accepte. Le strictement conforme
    serait schemeID « 0002 » (SIRENE) — à affiner si un validateur le refuse.
    """

    _inherit = "account.edi.xml.cii"

    def _export_invoice_vals(self, invoice):
        vals = super()._export_invoice_vals(invoice)
        company = invoice.company_id
        if company.country_id.code == "FR" and getattr(company, "siren", False):
            vals["seller_specified_legal_organization"] = company.siren
        return vals
