# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)

        for field_name in [
            "pack_ok",
            "pack_line_ids",
            "pack_type",
            "pack_component_price",
        ]:
            if field_name not in fields:
                fields.append(field_name)

        return fields
