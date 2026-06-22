# -*- coding: utf-8 -*-
{
    "name": "SuperPDP - Saxon schematron en sous-process",
    "version": "18.0.1.2.0",
    "summary": "Contourne le crash GraalVM/Saxon-C (saxonche) en sous-process ; "
               "émission Factur-X conforme PDP (vendeur SIREN, adresse "
               "destinataire scheme 0225 + SIREN).",
    "description": """
saxonche (Saxon-C / GraalVM) est fork/thread-unsafe : appelé depuis un worker
Odoo (mode threadé OU prefork), il lève une erreur native fatale
`graal_create_isolate` qui tue le process. Ce module monkeypatch
`pyfrctc._cdar_check_schematron` pour lancer la transformation XSLT 3.0 Saxon
dans un sous-process `python3` neuf (thread principal, sans fork hérité), ce qui
permet l'import des flux e-facture (réception) sans crash.

Émission (conformité PDP / SuperPDP) :
- surcharge `account.edi.xml.cii._export_invoice_vals` pour identifier le
  vendeur français par son SIREN (et non son SIRET) dans la Factur-X, sinon
  rejet 400 « L'entreprise (<SIREN>) ... ne correspond pas au vendeur (<SIRET>) ».
- surcharge `res.partner._compute_peppol_eas/_compute_peppol_endpoint` pour que
  l'adresse électronique de facturation FR soit `scheme 0225` (FRCTC) + SIREN,
  sinon rejet 400 « pre-check: receiver address does not exist in peppol directory ».
""",
    "author": "GottaPhish",
    "license": "LGPL-3",
    "depends": [
        "l10n_fr_einvoicing",
        "account_invoice_import_ubl",
        "account_edi_ubl_cii",
    ],
    "external_dependencies": {"python": ["pyfrctc", "saxonche"]},
    "installable": True,
}
