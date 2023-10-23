# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """We need to keep the discount defined on the components when checking out.
        Also when a line comes from a totalized pack, we should flag it to avoid
        changing it's price in a cart step."""
        line = self.env["sale.order.line"].browse(line_id)
        if line and line.pack_parent_line_id:
            pack = line.pack_parent_line_id.product_id
            detailed_totalized_pack = (
                pack.pack_type == "detailed"
                and pack.pack_component_price in {"totalized", "ignored"}
            )
            return super(
                SaleOrder,
                self.with_context(
                    pack_discount=line.discount,
                    detailed_totalized_pack=detailed_totalized_pack,
                ),
            )._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        return super()._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

    @api.depends("order_line.product_uom_qty", "order_line.product_id")
    def _compute_cart_info(self):
        """We only want to count the main pack line, not the component lines"""
        super()._compute_cart_info()
        for order in self:
            order.cart_quantity = int(
                sum(
                    order.website_order_line.filtered(
                        lambda x: not x.pack_parent_line_id
                    ).mapped("product_uom_qty")
                )
            )

    def _website_product_id_change(self, order_id, product_id, qty=0, **kwargs):
        """In the final checkout step, we could miss the component discount as the
        product prices are recomputed. We should also consider a forced price
        recomputation that would set a price on our detailed totalized pack lines
        duplicating the total price"""
        res = super(SaleOrder, self)._website_product_id_change(order_id, product_id, qty=qty,  **kwargs)
        if self.env.context.get("pack_discount"):
            res["discount"] = self.env.context.get("pack_discount")
        if self.env.context.get("detailed_totalized_pack"):
            res["price_unit"] = 0
        return res

    from odoo import models



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        """The website calls this method specifically. We want to get rid of
        the children lines so the user doesn't have to"""
        join_pack_children = self + self.mapped("pack_child_line_ids")
        return super(SaleOrderLine, join_pack_children.exists()).unlink()
