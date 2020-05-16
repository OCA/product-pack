# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pack_type = fields.Selection(related="product_id.pack_type",)
    pack_component_price = fields.Selection(
        related="product_id.pack_component_price",
    )

    # Fields for common packs
    pack_depth = fields.Integer(
        "Depth", help="Depth of the product if it is part of a pack."
    )
    pack_parent_line_id = fields.Many2one(
        "sale.order.line",
        "Pack",
        help="The pack that contains this product.",
        ondelete="cascade",
    )
    pack_child_line_ids = fields.One2many(
        "sale.order.line", "pack_parent_line_id", "Lines in pack"
    )

    def expand_pack_line(self, write=False):
        self.ensure_one()
        # if we are using update_pricelist or checking out on ecommerce we
        # only want to update prices
        do_not_expand = self._context.get(
            "update_prices"
        ) or self._context.get("update_pricelist", False)
        if (
            self.state == "draft"
            and self.product_id.pack_ok
            and self.pack_type == "detailed"
        ):
            for subline in self.product_id.get_pack_lines():
                vals = subline.get_sale_order_line_vals(self, self.order_id)
                vals["sequence"] = self.sequence
                if write:
                    existing_subline = self.search(
                        [
                            ("product_id", "=", subline.product_id.id),
                            ("pack_parent_line_id", "=", self.id),
                        ],
                        limit=1,
                    )
                    # if subline already exists we update, if not we create
                    if existing_subline:
                        if do_not_expand:
                            vals.pop("product_uom_qty")
                        existing_subline.write(vals)
                    elif not do_not_expand:
                        self.create(vals)
                else:
                    self.create(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.expand_pack_line()
        return record

    def write(self, vals):
        super().write(vals)
        if "product_id" in vals or "product_uom_qty" in vals:
            for record in self:
                record.expand_pack_line(write=True)

    def unlink(self):
        """Remove previously the pack children lines for avoiding issues in
        the cache.
        """
        # children = self.mapped("pack_child_line_ids")
        # if children:
        #     children.unlink()
        return super().unlink()

    def _get_real_price_currency(
        self, product, rule_id, qty, uom, pricelist_id
    ):
        new_list_price, currency_id = super()._get_real_price_currency(
            product, rule_id, qty, uom, pricelist_id
        )
        pack_types = {"totalized", "ignored"}
        parent_line = self.pack_parent_line_id
        if (
            parent_line
            and parent_line.pack_type == "details"
            and parent_line.pack_component_price in pack_types
        ):
            new_list_price = 0.0
        return new_list_price, currency_id

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom",
        "price_unit",
        "discount",
        "name",
        "tax_id",
    )
    def check_pack_line_modify(self):
        """ Do not let to edit a sale order line if this one belongs to pack
        """
        if (
            self._origin.pack_parent_line_id
            and not self._origin.pack_parent_line_id.product_id.pack_modifiable
        ):
            raise UserError(
                _(
                    "You can not change this line because is part of a pack"
                    " included in this order"
                )
            )

    def _get_display_price(self, product):
        # We do this to clean the price if the parent of the
        # component it's that type
        pack_types = {"totalized", "ignored"}
        parent_line = self.pack_parent_line_id
        if (
            parent_line.pack_type == "detailed"
            and parent_line.pack_component_price in pack_types
        ):
            return 0.0
        return super()._get_display_price(product)
