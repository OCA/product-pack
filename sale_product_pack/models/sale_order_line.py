# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import first


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _parent_name = "pack_parent_line_id"

    pack_type = fields.Selection(
        related="product_id.pack_type",
    )
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
    )
    pack_child_line_ids = fields.One2many(
        "sale.order.line", "pack_parent_line_id", "Lines in pack"
    )
    pack_modifiable = fields.Boolean(help="The parent pack is modifiable")

    do_no_expand_pack_lines = fields.Boolean(
        compute="_compute_do_no_expand_pack_lines",
        help="This is a technical field in order to check if pack lines has to be expanded",
    )

    @api.depends_context("update_prices", "update_pricelist")
    def _compute_do_no_expand_pack_lines(self):
        do_not_expand = self.env.context.get("update_prices") or self.env.context.get(
            "update_pricelist", False
        )
        self.update(
            {
                "do_no_expand_pack_lines": do_not_expand,
            }
        )

    def expand_pack_line(self, write=False):
        self.ensure_one()
        # if we are using update_pricelist or checking out on ecommerce we
        # only want to update prices
        vals_list = []
        if self.product_id.pack_ok and self.pack_type == "detailed":
            new_sequence = self.sequence + 1
            for subline in self.product_id.get_pack_lines():
                vals = subline.get_sale_order_line_vals(self, self.order_id)
                vals["sequence"] = new_sequence
                new_sequence += 1
                if write:
                    existing_subline = first(
                        self.pack_child_line_ids.filtered(
                            lambda child: child.product_id == subline.product_id
                        )
                    )
                    # if subline already exists we update, if not we create
                    if existing_subline:
                        if self.do_no_expand_pack_lines:
                            vals.pop("product_uom_qty", None)
                            vals.pop("discount", None)
                        existing_subline.write(vals)
                    elif not self.do_no_expand_pack_lines:
                        vals_list.append(vals)
                else:
                    vals_list.append(vals)
            if vals_list:
                self.create(vals_list)

    @api.model_create_multi
    def create(self, vals_list):
        new_vals = []
        res = self.browse()
        for elem in vals_list:
            product = self.env["product.product"].browse(elem.get("product_id"))
            if product and product.pack_ok and product.pack_type != "non_detailed":
                line = super().create([elem])
                line.expand_pack_line()
                res |= line
            else:
                new_vals.append(elem)
        res |= super().create(new_vals)
        return res

    def write(self, vals):
        res = super().write(vals)
        if "product_id" in vals or "product_uom_qty" in vals:
            for record in self:
                record.expand_pack_line(write=True)
        return res

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
        """Do not let to edit a sale order line if this one belongs to pack"""
        if self._origin.pack_parent_line_id and not self._origin.pack_modifiable:
            raise UserError(
                _(
                    "You can not change this line because is part of a pack"
                    " included in this order"
                )
            )

    def action_open_parent_pack_product_view(self):
        domain = [
            ("id", "in", self.mapped("pack_parent_line_id").mapped("product_id").ids)
        ]
        return {
            "name": _("Parent Product"),
            "type": "ir.actions.act_window",
            "res_model": "product.product",
            "view_type": "form",
            "view_mode": "tree,form",
            "domain": domain,
        }
