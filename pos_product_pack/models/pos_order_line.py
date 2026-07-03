# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    pack_parent_line_id = fields.Many2one(
        comodel_name="pos.order.line",
        string="Pack",
        help="The pack that contains this product.",
    )
    pack_child_line_ids = fields.One2many(
        comodel_name="pos.order.line",
        inverse_name="pack_parent_line_id",
        string="Lines in pack",
    )
    pack_line_id = fields.Many2one(
        comodel_name="product.pack.line",
        string="Pack Line",
    )

    @api.model
    def _load_pos_data_fields(self, config):
        loaded_fields = super()._load_pos_data_fields(config)
        return loaded_fields + [
            field
            for field in [
                "pack_parent_line_id",
                "pack_child_line_ids",
                "pack_line_id",
            ]
            if field not in loaded_fields
        ]
