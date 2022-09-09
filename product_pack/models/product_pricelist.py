# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        product = products_qty_partner[0][0]
        res = {}
        if (
            product.pack_ok
            and product.pack_type == "detailed"
            and product.pack_component_price == "totalized"
        ):
            res[product.id] = (product.price_compute("list_price")[product.id], False)
            return res
        else:
            return super()._compute_price_rule(
                products_qty_partner, date=date, uom_id=uom_id
            )
