# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductPackLine(models.Model):
    _name = "product.pack.line"
    _inherit = ["product.pack.line", "pos.load.mixin"]

    @api.model
    def _load_pos_data_fields(self, config):
        return [
            "id",
            "parent_product_id",
            "quantity",
            "product_id",
        ]

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [
            ("parent_product_id.available_in_pos", "=", True),
        ]
