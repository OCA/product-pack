# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update_line_quantity(
        self, line_id: int, quantity: float, **kwargs
    ) -> dict:
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
            )._cart_update_line_quantity(line_id, quantity, **kwargs)
        return super()._cart_update_line_quantity(line_id, quantity, **kwargs)

    def _prepare_order_line_update_values(self, order_line, quantity, **kwargs):
        """Preserve pack discount and handle detailed totalized packs"""
        values = super()._prepare_order_line_update_values(
            order_line, quantity, **kwargs
        )

        # If we have pack_discount in context, preserve it
        pack_discount = self.env.context.get("pack_discount")
        if pack_discount is not None and order_line.pack_parent_line_id:
            values["discount"] = pack_discount

        return values

    @api.depends("order_line.product_uom_qty", "order_line.product_id")
    def _compute_cart_info(self):
        """We only want to count the main pack line, not the component lines"""
        res = super()._compute_cart_info()
        for order in self:
            order.cart_quantity = int(
                sum(
                    order.website_order_line.filtered(
                        lambda x: not x.pack_parent_line_id
                    ).mapped("product_uom_qty")
                )
            )
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        """The website calls this method specifically. We want to get rid of
        the children lines so the user doesn't have to"""
        join_pack_children = self + self.mapped("pack_child_line_ids")
        return super(SaleOrderLine, join_pack_children.exists()).unlink()
