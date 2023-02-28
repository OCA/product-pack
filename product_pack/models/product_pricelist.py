# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products, qty, uom=None, date=False, **kwargs):
        """Don't call super when dealing with detailed and non detailed packs,
        as the computations done after calling `price_compute` modify the final returned
        price, so we compute it directly in these cases.
        """
        packs, no_packs = products.split_pack_products()
        res = super()._compute_price_rule(no_packs, qty, uom, date, **kwargs)
        for product in packs:
            res[product.id] = (
                product.price_compute("list_price")[product.id],
                False,
            )
        return res
