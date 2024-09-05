# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    pack_line_id = fields.Many2one(
        comodel_name="product.pack.line",
    )
