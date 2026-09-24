# -*- coding: utf-8 -*-
# La bascule "Saxon en sous-process" a été retirée : pyfrctc>=0.22 et
# factur-x>=6 n'utilisent plus saxonche (ils délèguent la transformation XSLT à
# un Saxon Server HTTP). Il ne reste que la normalisation UBL pour l'importeur
# OCA (account_invoice_import_ubl).
from . import models  # noqa: F401
