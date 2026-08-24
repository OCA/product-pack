# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError


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
        index=True,
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
        component lines grouped under a standard Odoo section.

        Nested packs in components are not expanded to avoid recursive expansions.
        """
        self.ensure_one()

        if (
            not self.product_id.pack_ok
            or self.pack_type != "non_detailed"
            or not self.product_id.pack_modifiable
        ):
            return self

        pack_lines = self.product_id.get_pack_lines()
        order = self.order_id
        base_sequence = self.sequence

        # Keep inserted lines contiguous under the section.
        # Shift the existing trailing lines to avoid sequence collisions.
        if pack_lines:
            shift = len(pack_lines) + 1
            for line in order.order_line.filtered(
                lambda order_line: order_line.id != self.id
                and order_line.sequence > base_sequence
            ).sorted("sequence", reverse=True):
                line.sequence += shift

        section_line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "display_type": "line_section",
                "name": self.product_id.display_name,
                "sequence": base_sequence,
                "collapse_composition": True,
            }
        )

        # Keep the pack product as the first editable line under the section.
        self.write(
            {
                "sequence": base_sequence + 1,
            }
        )
        created_lines = section_line + self

        # Create editable component lines
        for idx, pack_line in enumerate(pack_lines, start=2):
            component_vals = pack_line.get_sale_order_line_vals(self, order)
            component_vals.update(
                {
                    "sequence": base_sequence + idx,
                    # Standalone editable lines for non-detailed modifiable packs.
                    "pack_parent_line_id": False,
                    "pack_depth": 0,
                }
            )
            # Skip expansion for nested packs to avoid recursive expansions
            if pack_line.product_id.pack_ok:
                created_lines += (
                    self.env["sale.order.line"]
                    .with_context(skip_non_detailed_pack_transform=True)
                    .create(component_vals)
                )
            else:
                created_lines += self.env["sale.order.line"].create(component_vals)
        return created_lines

    def _get_non_detailed_pack_component_lines(self):
        self.ensure_one()
        component_lines = self.env["sale.order.line"]
        collect = False
        for line in self.order_id.order_line.sorted("sequence"):
            if line == self:
                collect = True
                continue
            if not collect:
                continue
            if line.display_type in ("line_section", "line_subsection"):
                break
            component_lines += line
        return component_lines

    def _get_non_detailed_pack_section_line(self):
        """Return the section line (collapse_composition) that heads this pack group."""
        self.ensure_one()
        candidates = self.order_id.order_line.filtered(
            lambda sol: sol.sequence < self.sequence
            and sol.display_type == "line_section"
            and sol.collapse_composition
        )
        return candidates.sorted("sequence", reverse=True)[:1]

    def _sync_non_detailed_pack_component_qty(self):
        """Sync component quantities with the pack product quantity."""
        self.ensure_one()
        if (
            self.display_type
            or not self.product_id.pack_ok
            or self.pack_type != "non_detailed"
            or not self.product_id.pack_modifiable
        ):
            return

        components = self._get_non_detailed_pack_component_lines().filtered(
            lambda line: not line.display_type
        )
        for pack_line in self.product_id.get_pack_lines():
            expected_qty = pack_line.quantity * self.product_uom_qty
            component_line = components.filtered(
                lambda line, product=pack_line.product_id: line.product_id == product
            )[:1]
            if component_line:
                component_line.product_uom_qty = expected_qty

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
                    record._sync_non_detailed_pack_component_qty()
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
        "tax_ids",
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
        tmpl = self.product_id.product_tmpl_id
        if (
            tmpl.pack_ok
            and tmpl.pack_type == "non_detailed"
            and tmpl.pack_modifiable
            and not self.display_type
        ):
            # Non-detailed modifiable pack expanded into standalone lines:
            # the pack line shows only its own base price; each component
            # carries its real price separately. Use pack_base_price_only to
            # bypass the totalization logic in product_pricelist._get_product_price.
            return self.order_id.pricelist_id.with_context(
                pack_base_price_only=True
            )._get_product_price(product=tmpl, quantity=1.0)
        price = super()._get_pricelist_price()
        if tmpl._is_pack_to_be_handled():
            price = self.order_id.pricelist_id._get_product_price(
                product=tmpl, quantity=1.0
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

    def _get_non_detailed_modifiable_pack_line(self):
        """Return the product line of the non-detailed modifiable pack that heads
        this standalone component line, or an empty recordset when it is not such a
        component.

        These lines carry ``pack_modifiable=True`` but no ``pack_parent_line_id``
        (they were detached on expansion), so the originating pack is recovered
        through the collapsible section that heads the group.
        """
        self.ensure_one()
        if self.display_type or self.pack_parent_line_id or not self.pack_modifiable:
            return self.env["sale.order.line"]
        section_line = self._get_non_detailed_pack_section_line()
        if not section_line:
            return self.env["sale.order.line"]
        # The pack product line is the first editable line under the section.
        pack_line = section_line._get_non_detailed_pack_component_lines().filtered(
            lambda sol: not sol.display_type
            and sol.product_id.pack_ok
            and sol.pack_type == "non_detailed"
            and sol.product_id.pack_modifiable
        )[:1]
        # The heading line itself is the pack, not one of its components.
        if not pack_line or pack_line == self:
            return self.env["sale.order.line"]
        return pack_line

    def _is_non_detailed_modifiable_component(self):
        self.ensure_one()
        return bool(self._get_non_detailed_modifiable_pack_line())

    def _get_non_detailed_modifiable_discount(self):
        """Discount carried by the originating ``product.pack.line.sale_discount``,
        composed with any manual discount on the line (same formula as
        :meth:`_get_pack_line_discount`).
        """
        self.ensure_one()
        pack_line = self._get_non_detailed_modifiable_pack_line()
        discount = self.discount
        for product_pack_line in pack_line.product_id.pack_line_ids:
            if product_pack_line.product_id == self.product_id:
                discount = 100.0 - (
                    (100.0 - self.discount)
                    * (100.0 - product_pack_line.sale_discount)
                    / 100.0
                )
                break
        return discount

    @api.depends("product_id", "product_uom_id", "product_uom_qty")
    def _compute_discount(self):
        res = super()._compute_discount()
        for pack_line in self.filtered("pack_parent_line_id"):
            pack_line.discount = pack_line._get_pack_line_discount()
        for line in self.filtered(
            lambda sol: sol._is_non_detailed_modifiable_component()
        ):
            line.discount = line._get_non_detailed_modifiable_discount()
        return res

    def _compute_name(self):
        res = super()._compute_name()
        for line in self:
            parent = line.pack_parent_line_id
            if parent.product_id.pack_ok and parent.pack_type == "detailed":
                line.name = f"{'> ' * (parent.pack_depth + 1)}{line.name}"
        return res

    def _compute_price_unit(self):
        # Avoid recomputing prices for pack component lines whose price must remain
        # handled by the parent pack line, as some enterprise modules may trigger
        # price recomputation and override their expected zero price.
        lines_to_recompute = self.filtered(
            lambda line: not (
                line.pack_parent_line_id
                and line.pack_parent_line_id.product_id.pack_component_price
                in ("totalized", "ignored")
            )
        )
        return super(SaleOrderLine, lines_to_recompute)._compute_price_unit()
