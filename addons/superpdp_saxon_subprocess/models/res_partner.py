# -*- coding: utf-8 -*-
from odoo import models


class ResPartner(models.Model):
    """Adresse électronique de facturation FR = scheme 0225 (FRCTC) + SIREN.

    Le pré-contrôle d'émission du SuperPDP recherche le destinataire par son
    adresse électronique de facturation. En France, celle-ci est le **SIREN**
    sous le scheme **0225** (« France FRCTC Electronic Address ») :

        <ram:URIUniversalCommunication>
            <ram:URIID schemeID="0225">843228636</ram:URIID>
        </ram:URIUniversalCommunication>

    Odoo natif (`account_edi_ubl_cii`) calcule par défaut `peppol_eas` à 0009
    (SIRET) ou 9957 (TVA) pour la France, d'où le rejet :
        400 CREATE_ERROR - « pre-check: receiver address does not exist in
        peppol directory ».

    On force donc, pour les partenaires FR disposant d'un SIREN,
    `peppol_eas=0225` et `peppol_endpoint=<SIREN>`.

    NB : ces champs sont calculés-stockés (recalcul si pays/TVA/RCS changent) ;
    cet override garantit la valeur correcte au fil des recalculs et pour les
    nouveaux partenaires.
    """

    _inherit = "res.partner"

    def _compute_peppol_eas(self):
        super()._compute_peppol_eas()
        for partner in self:
            if partner.country_code == "FR" and getattr(partner, "siren", False):
                partner.peppol_eas = "0225"

    def _compute_peppol_endpoint(self):
        super()._compute_peppol_endpoint()
        for partner in self:
            if (
                partner.country_code == "FR"
                and partner.peppol_eas == "0225"
                and getattr(partner, "siren", False)
            ):
                partner.peppol_endpoint = partner.siren
