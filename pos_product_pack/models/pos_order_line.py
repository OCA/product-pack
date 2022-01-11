# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    pack_parent_line_id = fields.Many2one(
        "pos.order.line",
        "Pack",
        help="The pack that contains this product.",
    )
    pack_child_line_ids = fields.One2many(
        "pos.order.line", "pack_parent_line_id", "Lines in pack"
    )
