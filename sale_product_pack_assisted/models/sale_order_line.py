# Copyright 2019 ADHOC SA - Juan José Scarafía
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


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
        "assisted_pack_line_ids",
        "assisted_pack_line_ids.price_subtotal",
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
        do_not_expand = self.env.context.get("update_prices") or self.env.context.get(
            "update_pricelist", False
        )
        if not do_not_expand and self.product_id.pack_type == "non_detailed_assisted":
            # remove previus existing lines
            self.assisted_pack_line_ids.unlink()

            # create a sale pack line for each product pack line
            for pack_line in self.product_id.pack_line_ids.with_context(
                pricelist=self.order_id.pricelist_id.id
            ):
                price_unit = pack_line.product_id._get_contextual_price()
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
        return super().expand_pack_line(write)

    def action_assisted_pack_detail(self):
        view = self.env.ref("sale_product_pack_assisted.view_order_line_form2")
        return {
            "name": self.env._("Details"),
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

    def action_transform_pack_to_lines(self):
        """
        Transform the assisted pack line into detailed lines:
        1. Create a section line with the pack product name
        2. Create individual lines for each component with their qty and discount
        3. Delete the original pack line
        """
        self.ensure_one()

        if self.product_id.pack_type != "non_detailed_assisted":
            return
        pack_name = self.product_id.display_name
        pack_sequence = self.sequence
        order = self.order_id

        # Prepare values for section line
        section_vals = {
            "order_id": order.id,
            "display_type": "line_section",
            "name": pack_name,
            "sequence": pack_sequence,
            "collapse_composition": True,
        }
        self.env["sale.order.line"].create(section_vals)

        # Create lines for each component from assisted_pack_line_ids
        for idx, pack_line in enumerate(self.assisted_pack_line_ids, start=1):
            component_vals = {
                "order_id": order.id,
                "product_id": pack_line.product_id.id,
                "product_uom_qty": pack_line.product_uom_qty,
                "price_unit": pack_line.price_unit,
                "discount": pack_line.discount,
                "sequence": pack_sequence + idx,
            }
            self.env["sale.order.line"].create(component_vals)

        # Delete the original pack line
        self.unlink()
        return {"type": "ir.actions.act_window_close"}
