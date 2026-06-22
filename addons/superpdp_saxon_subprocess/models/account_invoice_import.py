# -*- coding: utf-8 -*-
"""Normalize prefix-less UBL before the OCA parser.

SuperPDP's `generate_test_invoice?format=ubl` emits valid UBL but redeclares the
default namespace on every element (no `cbc:`/`cac:` prefixes). OCA
`account_invoice_import_ubl.parse_ubl_invoice` derives its XPath namespace map
from `xml_root.nsmap`, which then lacks `cbc`/`cac`, so `//cbc:UBLVersionID`
raises `XPathEvalError: Undefined namespace prefix`.

We rebuild the tree with the standard UBL prefixes declared at the root, then
delegate to the original parser (all its `cbc:`/`cac:` XPaths resolve by URI).
"""
import logging

from lxml import etree

from odoo import api, models

_logger = logging.getLogger(__name__)

_UBL_NSMAP = {
    None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
    "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}


def _normalize_ubl(xml_root):
    """Return an equivalent tree whose root declares standard UBL prefixes."""
    if "cbc" in (xml_root.nsmap or {}):
        return xml_root  # already prefixed -> nothing to do
    new_root = etree.Element(xml_root.tag, nsmap=_UBL_NSMAP)
    new_root.text = xml_root.text
    for attr, val in xml_root.attrib.items():
        new_root.set(attr, val)

    def _copy(src, dst):
        for child in src:
            if not isinstance(child.tag, str):  # skip comments / PIs
                continue
            sub = etree.SubElement(dst, child.tag)
            sub.text = child.text
            sub.tail = child.tail
            for attr, val in child.attrib.items():
                sub.set(attr, val)
            _copy(child, sub)

    _copy(xml_root, new_root)
    return new_root


class AccountInvoiceImport(models.TransientModel):
    _inherit = "account.invoice.import"

    @api.model
    def parse_ubl_invoice(self, xml_root, company):
        try:
            xml_root = _normalize_ubl(xml_root)
        except Exception as e:  # noqa: BLE001 - never block on normalization
            _logger.warning("UBL normalization skipped: %s", e)
        return super().parse_ubl_invoice(xml_root, company)
