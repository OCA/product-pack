# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        if "pack_ok" not in fields:
            fields.append("pack_ok")
        return fields
