# Copyright 2019 ADHOC SA - Juan José Scarafía
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pack_type = fields.Selection(
        selection_add=[("non_detailed_assisted", "Non Detailed - Assisted")],
        help="On sale orders or purchase orders:\n"
        "* Detailed: Display components individually in the sale order.\n"
        "* Non Detailed: Do not display components individually in the"
        " sale order.\n"
        "* Non Detailed - Assisted: Do not display components individually in the"
        " sale order but gives a template that user can edit to calculate pack amount",
    )
