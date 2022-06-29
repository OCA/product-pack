# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if (
            record.product_id.pack_ok
            and record.product_id.pack_component_price == "totalized"
        ):
            record.product_uom_change()
        return record
