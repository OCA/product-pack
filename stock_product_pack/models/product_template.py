# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dont_create_move = fields.Boolean(
        string="Don't create move",
        help="With this option, the pack won't create an stock.move and will"
        " be set as delivered upon sale confirmation. This is useful to use "
        "get pack stock availability (type = 'product') but"
        " without actually having stock and moves of it.",
    )
