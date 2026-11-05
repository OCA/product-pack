from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def pack_cost_compute(self, line):
        """This function computes the cost of a product based on the options on pack"""
        packs, no_packs = self.split_pack_products()
        prices = {}
        for product in packs.with_context(prefetch_fields=False):
            pack_price = 0.0
            for pack_line in product.sudo().pack_line_ids:
                pack_price += pack_line.get_seller_cost(line)
            prices[product.id] = pack_price
        return prices
