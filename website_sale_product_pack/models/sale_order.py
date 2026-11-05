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

    def _cart_accessories(self):
        """Judge the suggested packs by their whole price"""
        return super(
            SaleOrder, self.with_context(whole_pack_price=True)
        )._cart_accessories()

    def _get_zero_priced_lines(self):
        """The lines of a pack are zero priced only when the whole pack is. Its
        components go at 0 on purpose when the main line holds the price."""
        lines = super()._get_zero_priced_lines()
        return lines.filtered(
            lambda line: not line._get_pack_root_line() or line._is_pack_zero_priced()
        )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        """The website calls this method specifically. We want to get rid of
        the children lines so the user doesn't have to"""
        join_pack_children = self + self.mapped("pack_child_line_ids")
        return super(SaleOrderLine, join_pack_children.exists()).unlink()

    def _get_pack_root_line(self):
        """Return the top pack line this line belongs to, or an empty
        recordset when the line is not part of a pack"""
        self.ensure_one()
        if not (self.pack_parent_line_id or self.pack_child_line_ids):
            return self.browse()
        line = self
        while line.pack_parent_line_id:
            line = line.pack_parent_line_id
        return line

    def _get_pack_lines(self):
        """Return all the lines of the pack of this line, at any depth"""
        lines = children = self._get_pack_root_line()
        while children:
            children = children.pack_child_line_ids
            lines |= children
        return lines

    def _is_pack_zero_priced(self):
        """Whether the whole pack of this line has no price"""
        return not any(self._get_pack_lines().mapped("price_unit"))

    def _get_lines_with_price(self):
        if self.env.context.get("whole_pack_lines") and self._get_pack_root_line():
            return self._get_pack_lines()
        return super()._get_lines_with_price()

    def _check_validity(self):
        """Check the price of the whole pack, as the core does with combos"""
        return super(
            SaleOrderLine, self.with_context(whole_pack_lines=True)
        )._check_validity()
