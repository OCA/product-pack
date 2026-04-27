# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _parent_name = "pack_parent_line_id"

    pack_is_visual_header = fields.Boolean(
        help="Whether this line acts as a section-like header for pack components."
    )

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
        help="This is a technical field in order to check if pack lines has to be "
        "expanded",
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
            for subline in self.product_id.get_pack_lines():
                vals = subline.get_sale_order_line_vals(self, self.order_id)
                if write:
                    existing_subline = (
                        self.pack_child_line_ids.filtered(
                            lambda child, s=subline: child.product_id == s.product_id
                        )
                    )[:1]
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

    def action_transform_pack_to_lines(self):
        """
        Transform non_detailed pack with pack_modifiable into editable
        component lines while keeping the original pack line as a visual
        header with collapse behavior.
        """
        self.ensure_one()

        if (
            not self.product_id.pack_ok
            or self.pack_type != "non_detailed"
            or not self.product_id.pack_modifiable
            or self.pack_is_visual_header
        ):
            return self

        # Keep nested packs unexpanded to avoid recursive/non-intuitive expansions.
        pack_lines = self.product_id.get_pack_lines()
        if any(line.product_id.pack_ok for line in pack_lines):
            return self

        order = self.order_id
        base_sequence = self.sequence

        # Keep the pack line and mark it as section-like visual header.
        self.write(
            {
                "name": self.product_id.display_name,
                "pack_is_visual_header": True,
                "collapse_composition": True,
                "price_unit": 0.0,
                "discount": 0.0,
            }
        )
        created_lines = self

        # Create editable component lines
        for idx, pack_line in enumerate(pack_lines, start=1):
            component_vals = pack_line.get_sale_order_line_vals(self, order)
            component_vals.update(
                {
                    "sequence": base_sequence + idx,
                    # Standalone editable lines for non-detailed modifiable packs.
                    "pack_parent_line_id": False,
                    "pack_depth": 0,
                }
            )
            created_lines += self.env["sale.order.line"].create(component_vals)
        return created_lines

    def _sync_visual_header_component_qty(self):
        """Sync component quantities with the visual header pack quantity."""
        self.ensure_one()
        if (
            not self.pack_is_visual_header
            or not self.product_id.pack_ok
            or self.pack_type != "non_detailed"
            or not self.product_id.pack_modifiable
        ):
            return

        components = self._get_section_lines().filtered(
            lambda line: not line.display_type and not line.pack_is_visual_header
        )
        for pack_line in self.product_id.get_pack_lines():
            expected_qty = pack_line.quantity * self.product_uom_qty
            component_line = components.filtered(
                lambda line, product=pack_line.product_id: line.product_id == product
            )[:1]
            if component_line:
                component_line.product_uom_qty = expected_qty

    def _compute_parent_id(self):
        res = super()._compute_parent_id()
        sale_order_lines = set(self)
        for order, _lines in self.grouped("order_id").items():
            if not order:
                continue
            last_section = False
            last_sub = False
            for line in order.order_line.sorted("sequence"):
                if line.display_type == "line_section" or line.pack_is_visual_header:
                    last_section = line
                    if line in sale_order_lines:
                        line.parent_id = False
                    last_sub = False
                elif line.display_type == "line_subsection":
                    if line in sale_order_lines:
                        line.parent_id = last_section
                    last_sub = line
                elif line in sale_order_lines:
                    line.parent_id = last_sub or last_section
            return res

    @api.model_create_multi
    def create(self, vals_list):
        """Only when strictly necessary (a product is a pack) will be created line
        by line, this is necessary to maintain the correct order.
        """
        product_ids = [elem.get("product_id") for elem in vals_list]
        products = self.env["product.product"].browse(product_ids)
        if any(
            p.pack_ok
            and (
                p.pack_type == "detailed"
                or (p.pack_type == "non_detailed" and p.pack_modifiable)
            )
            for p in products
        ):
            res = self.browse()
            for elem in vals_list:
                line = super().create([elem])
                product = line.product_id
                if product and product.pack_ok:
                    if product.pack_type == "detailed":
                        res += line
                        line.expand_pack_line()
                    elif (
                        product.pack_type == "non_detailed" and product.pack_modifiable
                    ):
                        if self.env.context.get("skip_non_detailed_pack_transform"):
                            res += line
                        else:
                            res += line.action_transform_pack_to_lines()
                else:
                    res += line
            return res
        else:
            return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "product_id" in vals or "product_uom_qty" in vals:
            for record in self:
                record.expand_pack_line(write=True)
                if "product_uom_qty" in vals:
                    record._sync_visual_header_component_qty()
                if (
                    "product_id" in vals
                    and record.product_id.pack_ok
                    and record.pack_type == "non_detailed"
                    and record.product_id.pack_modifiable
                ):
                    record.action_transform_pack_to_lines()
        return res

    @api.onchange(
        "product_id",
        "product_uom_qty",
        "product_uom_id",
        "price_unit",
        "discount",
        "name",
        "tax_id",
    )
    def check_pack_line_modify(self):
        """Do not let to edit a sale order line if this one belongs to pack"""
        if self._origin.pack_parent_line_id and not self._origin.pack_modifiable:
            raise UserError(
                self.env._(
                    "You can not change this line because is part of a pack"
                    " included in this order"
                )
            )

    def action_open_parent_pack_product_view(self):
        domain = [
            ("id", "in", self.mapped("pack_parent_line_id").mapped("product_id").ids)
        ]
        return {
            "name": self.env._("Parent Product"),
            "type": "ir.actions.act_window",
            "res_model": "product.product",
            "view_type": "form",
            "view_mode": "list,form",
            "domain": domain,
        }

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        price = super()._get_pricelist_price()

        if self.product_id.product_tmpl_id._is_pack_to_be_handled():
            price = self.order_id.pricelist_id._get_product_price(
                product=self.product_id.product_tmpl_id, quantity=1.0
            )
        return price

    def _get_pack_line_discount(self):
        """returns the discount settled in the parent pack lines"""
        self.ensure_one()
        discount = 0.0
        if self.pack_parent_line_id.pack_component_price == "detailed":
            for pack_line in self.pack_parent_line_id.product_id.pack_line_ids:
                if pack_line.product_id == self.product_id:
                    discount = 100.0 - (
                        (100.0 - self.discount)
                        * (100.0 - pack_line.sale_discount)
                        / 100.0
                    )
                    break
        return discount

    @api.depends("product_id", "product_uom_id", "product_uom_qty")
    def _compute_discount(self):
        res = super()._compute_discount()
        for pack_line in self.filtered("pack_parent_line_id"):
            pack_line.discount = pack_line._get_pack_line_discount()
        return res

    def _compute_name(self):
        res = super()._compute_name()
        for line in self:
            parent = line.pack_parent_line_id
            if parent.product_id.pack_ok and parent.pack_type == "detailed":
                line.name = f"{'> ' * (parent.pack_depth + 1)}{line.name}"
        return res
