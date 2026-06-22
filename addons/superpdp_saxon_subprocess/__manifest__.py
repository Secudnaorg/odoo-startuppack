# -*- coding: utf-8 -*-
{
    "name": "SuperPDP - Saxon schematron en sous-process",
    "version": "18.0.1.0.0",
    "summary": "Contourne le crash GraalVM/Saxon-C (saxonche) en exécutant la "
               "validation schematron CDAR dans un sous-process Python neuf.",
    "description": """
saxonche (Saxon-C / GraalVM) est fork/thread-unsafe : appelé depuis un worker
Odoo (mode threadé OU prefork), il lève une erreur native fatale
`graal_create_isolate` qui tue le process. Ce module monkeypatch
`pyfrctc._cdar_check_schematron` pour lancer la transformation XSLT 3.0 Saxon
dans un sous-process `python3` neuf (thread principal, sans fork hérité), ce qui
permet l'import des flux e-facture (réception) sans crash.
""",
    "author": "GottaPhish",
    "license": "LGPL-3",
    "depends": ["l10n_fr_einvoicing", "account_invoice_import_ubl"],
    "external_dependencies": {"python": ["pyfrctc", "saxonche"]},
    "installable": True,
}
