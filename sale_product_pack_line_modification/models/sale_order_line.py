# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pack_modified_line = fields.Boolean()

    def action_sale_product_pack_modification(self):
        """
        Launch the wizard to allow product modification
        """
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sale_product_pack_line_modification.sale_product_pack_line_modification_act_window"
        )
        action["context"] = {"active_ids": self.ids, "active_model": "sale.order.line"}

        return action

    def action_sale_product_pack_modified(self):
        pass
