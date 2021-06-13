# Copyright 2019 ADHOC SA - Juan José Scarafía
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    assisted_pack_line_ids = fields.One2many(
        "sale.order.line.pack.line", "order_line_id", "Assisted Pack Lines"
    )
    assisted_pack_total = fields.Float(compute="_compute_assisted_pack_total")

    @api.onchange("assisted_pack_total")
    def _onchange_pack_line_ids(self):
        for line in self:
            line.price_unit = line.assisted_pack_total

    @api.depends(
        "assisted_pack_line_ids", "assisted_pack_line_ids.price_subtotal",
    )
    def _compute_assisted_pack_total(self):
        for line in self:
            line.assisted_pack_total = sum(
                x.price_subtotal for x in line.assisted_pack_line_ids
            )

    def expand_pack_line(self, write=False):
        self.ensure_one()
        # if we are using update_pricelist or checking out on ecommerce we
        # only want to update prices
        do_not_expand = self._context.get("update_prices") or self._context.get(
            "update_pricelist", False
        )
        if not do_not_expand and self.product_id.pack_type == "non_detailed_assisted":
            # remove previus existing lines
            self.assisted_pack_line_ids.unlink()

            # create a sale pack line for each product pack line
            for pack_line in self.product_id.pack_line_ids.with_context(
                pricelist=self.order_id.pricelist_id.id
            ):
                price_unit = pack_line.product_id.price
                quantity = pack_line.quantity
                vals = {
                    "order_line_id": self.id,
                    "product_id": pack_line.product_id.id,
                    "product_uom_qty": quantity,
                    "price_unit": price_unit,
                    "discount": pack_line.sale_discount,
                    "price_subtotal": price_unit * quantity,
                }
                self.assisted_pack_line_ids.create(vals)
        return super().expand_pack_line()

    def action_assisted_pack_detail(self):
        view = self.env.ref("sale_product_pack_assisted.view_order_line_form2")
        return {
            "name": _("Details"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order.line",
            "view_id": view.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "readonly": True,
            "res_id": self.id,
            "context": dict(self.env.context, pricelist=self.order_id.pricelist_id.id),
        }

    def button_save_data(self):
        return True
