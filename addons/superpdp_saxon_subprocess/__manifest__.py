# -*- coding: utf-8 -*-
{
    "name": "SuperPDP - Normalisation UBL import",
    "version": "18.0.2.0.0",
    "summary": "Normalise l'UBL sans préfixes (SuperPDP) avant l'importeur OCA.",
    "description": """
Historiquement, ce module contournait aussi le crash GraalVM/Saxon-C (saxonche)
en exécutant la validation schematron dans un sous-process Python neuf. Ce
contournement est désormais INUTILE : pyfrctc>=0.22 et factur-x>=6 délèguent la
transformation XSLT à un Saxon Server HTTP (plus de saxonche in-process).

Il ne reste que la normalisation de l'UBL sans préfixes émis par SuperPDP
(`generate_test_invoice?format=ubl`), qui casse le parseur OCA
`account_invoice_import_ubl` (XPath `cbc:`/`cac:` non résolus).
""",
    "author": "GottaPhish",
    "license": "LGPL-3",
    "depends": ["l10n_fr_einvoicing", "account_invoice_import_ubl"],
    "installable": True,
}
