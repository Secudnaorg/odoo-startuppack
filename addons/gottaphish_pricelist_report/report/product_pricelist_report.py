# -*- coding: utf-8 -*-
from odoo import models


class ReportProductPricelist(models.AbstractModel):
    _inherit = "report.product.report_pricelist"

    def _get_product_data(self, is_product_tmpl, product, pricelist, quantities):
        """Expose the sales description and internal reference to the QWeb
        pricelist template (the core method only passes id/name/price/uom)."""
        data = super()._get_product_data(
            is_product_tmpl, product, pricelist, quantities
        )
        data["description_sale"] = product.description_sale or ""
        data["default_code"] = product.default_code or ""
        return data
