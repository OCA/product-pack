# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleProductPackLineModification(models.TransientModel):

    _name = "sale.product.pack.line.modification"
    _description = "Sale Product Pack Line Modification"

    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
    )
    sale_order_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        required=True,
        ondelete="cascade",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids")
        if active_ids and self.env.context.get("active_model") == "sale.order.line":
            res.update({"sale_order_line_ids": [(6, 0, active_ids)]})

        return res

    def _post_change(self, line, old_product):
        """
        Add a message on sale order with changes
        """
        line.order_id.message_post(
            body=_("A line has been changed from product (%s) to product (%s)")
            % (old_product.display_name, line.product_id.display_name)
        )

    def _prepare_order_line(self, line):
        """
        Use a fake memory record for product pack line in order
        to use the prepare function to retrieve sale order line values
        """
        self.ensure_one()
        new_pack_line = self.env["product.pack.line"].new(
            {
                "parent_product_id": line.pack_parent_line_id.product_id.id,
                "product_id": self.product_id,
            }
        )
        vals = new_pack_line.get_sale_order_line_vals(
            line.pack_parent_line_id, line.order_id
        )
        vals.update(
            {
                "pack_modified_line": True,
            }
        )
        return vals

    def doit(self):
        for wizard in self:
            for line in wizard.sale_order_line_ids:
                old_product = line.product_id
                vals = wizard._prepare_order_line(line)
                line.write(vals)
                wizard._post_change(line, old_product)
        return True
