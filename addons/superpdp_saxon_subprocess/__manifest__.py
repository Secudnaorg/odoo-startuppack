# -*- coding: utf-8 -*-
{
    "name": "SuperPDP - Saxon schematron en sous-process",
    "version": "18.0.1.1.0",
    "summary": "Contourne le crash GraalVM/Saxon-C (saxonche) en sous-process, et "
               "émet le SIREN comme identifiant légal vendeur Factur-X (PDP).",
    "description": """
saxonche (Saxon-C / GraalVM) est fork/thread-unsafe : appelé depuis un worker
Odoo (mode threadé OU prefork), il lève une erreur native fatale
`graal_create_isolate` qui tue le process. Ce module monkeypatch
`pyfrctc._cdar_check_schematron` pour lancer la transformation XSLT 3.0 Saxon
dans un sous-process `python3` neuf (thread principal, sans fork hérité), ce qui
permet l'import des flux e-facture (réception) sans crash.

Émission : surcharge `account.edi.xml.cii._export_invoice_vals` pour identifier
le vendeur français par son SIREN (et non son SIRET) dans la Factur-X, afin que
l'identifiant corresponde au compte/à la session PDP (SuperPDP), sinon rejet
400 « L'entreprise (<SIREN>) ... ne correspond pas au vendeur (<SIRET>) ».
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
