# -*- coding: utf-8 -*-
{
    "name": "GottaPhish - Description vente dans le rapport tarif",
    "version": "18.0.1.0.0",
    "summary": "Ajoute la description du devis (description_sale) et la "
               "reference interne dans l'impression des listes de prix.",
    "description": """
Le rapport standard d'impression des listes de prix
(`report.product.report_pricelist`) ne transmet au template QWeb que
`id`, `name`, `price` et `uom` pour chaque produit. La description de vente
n'est donc pas affichable.

Ce module surcharge `_get_product_data` pour ajouter `description_sale` et
`default_code` au dictionnaire, et etend le template `report_pricelist_page`
pour afficher la description sous le nom du produit.
""",
    "author": "GottaPhish",
    "license": "LGPL-3",
    "category": "Sales/Sales",
    "depends": ["product"],
    "data": [
        "report/report_pricelist_templates.xml",
    ],
    "installable": True,
}
