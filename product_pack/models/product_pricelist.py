# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """Don't call super when dealing with detailed and non detailed packs,
        as the computations done after calling `price_compute` modify the final returned
        price, so we compute it directly in these cases.
        """
        products_qty_partner_super = [
            (s[0], s[1], s[2])
            for s in products_qty_partner
            if not s[0] in s[0].split_pack_products()[0]
        ]
        res = super()._compute_price_rule(
            products_qty_partner_super, date=date, uom_id=uom_id
        )
        for product, _, _ in products_qty_partner:
            if product in product.split_pack_products()[0]:
                res[product.id] = (
                    product.price_compute("list_price")[product.id],
                    False,
                )
        return res
