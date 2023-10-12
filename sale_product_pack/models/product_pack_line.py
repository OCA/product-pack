# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductPack(models.Model):
    _inherit = "product.pack.line"

    sale_discount = fields.Float(
        "Sale discount (%)",
        digits="Discount",
    )

    def get_sale_order_line_vals(self, line, order):
        self.ensure_one()
        quantity = self.quantity * line.product_uom_qty
        line_vals = {
            "order_id": order.id,
            "sequence": line.sequence,
            "product_id": self.product_id.id or False,
            "pack_parent_line_id": line.id,
            "pack_depth": line.pack_depth + 1,
            "company_id": order.company_id.id,
            "pack_modifiable": line.product_id.pack_modifiable,
            "product_uom_qty": quantity,
        }
        sol = line.new(line_vals)
        sol._onchange_product_id_warning()
        vals = sol._convert_to_write(sol._cache)
        pack_price_types = {"totalized", "ignored"}
        if (
            line.product_id.pack_type == "detailed"
            and line.product_id.pack_component_price in pack_price_types
        ):
            vals["price_unit"] = 0.0

        vals["name"] = f"{'> ' * (line.pack_depth + 1)}{sol.name}"

        return vals

    def _get_pack_line_price(self, pricelist, quantity, uom=None, date=False, **kwargs):
        return super()._get_pack_line_price(
            pricelist, quantity, uom=uom, date=date, **kwargs
        ) * (1 - self.sale_discount / 100.0)

    def _pack_line_price_compute(
        self, price_type, uom=False, currency=False, company=False, date=False
    ):
        pack_line_prices = super()._pack_line_price_compute(
            price_type, uom, currency, company, date
        )
        for line in self:
            pack_line_prices[line.product_id.id] *= 1 - line.sale_discount / 100.0
        return pack_line_prices
