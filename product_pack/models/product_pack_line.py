# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPackLine(models.Model):
    _name = "product.pack.line"
    _description = "Product pack line"
    _rec_name = "product_id"

    parent_product_id = fields.Many2one(
        "product.product",
        "Parent Product",
        ondelete="cascade",
        index=True,
        required=True,
    )
    quantity = fields.Float(
        required=True,
        default=1.0,
        digits="Product UoS",
    )
    product_id = fields.Many2one(
        "product.product",
        "Product",
        ondelete="cascade",
        index=True,
        required=True,
    )

    # because on expand_pack_line we are searching for existing product, we
    # need to enforce this condition
    _sql_constraints = [
        (
            "product_uniq",
            "unique(parent_product_id, product_id)",
            "Product must be only once on a pack!",
        ),
    ]

    @api.constrains("product_id")
    def _check_recursion(self):
        """Check recursion on packs."""
        for line in self:
            parent_product = line.parent_product_id
            pack_lines = line
            while pack_lines:
                if parent_product in pack_lines.mapped("product_id"):
                    raise ValidationError(
                        _("You cannot set recursive packs.\nProduct id: %s")
                        % parent_product.id
                    )
                pack_lines = pack_lines.mapped("product_id.pack_line_ids")

    def get_price(self, price_type=None, currency=False, company=False, date=False):
        self.ensure_one()
        if price_type and price_type == "standard_price":
            price_currency = self.product_id.cost_currency_id
            company = company or self.env.company
            date = date or fields.Date.context_today(self)
            price = self.product_id["standard_price"]
            if price_currency != currency:
                price = price_currency._convert(price, currency, company, date)
            return price * self.quantity
        return self.product_id.lst_price * self.quantity
