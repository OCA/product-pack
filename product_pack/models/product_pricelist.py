from odoo import models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_product_price(self, product, quantity, uom=None, date=False, **kwargs):
        """Compute the pricelist price for the specified pack product, qty & uom.

        :returns: unit price of the pack product + components, considering pricelist rules
        """
        self.ensure_one()
        if product._is_pack_to_be_handled():
            pack_price = self._compute_price_rule(
                product, quantity, uom=uom, date=date, **kwargs
            )[product.id][0]

            for line in product.sudo().pack_line_ids:
                pack_price += line._get_pack_line_price(
                    self, quantity, uom=uom, date=date, **kwargs
                )
            return pack_price
        else:
            return super()._get_product_price(
                product=product, quantity=quantity, uom=uom, date=date, **kwargs
            )

    def _get_products_price(self, products, quantity, uom=None, date=False, **kwargs):
        """Compute the pricelist price for the specified pack product, qty & uom.

        :returns: unit price of the pack product + components, considering pricelist rules
        """
        packs, no_packs = products.split_pack_products()
        res = super()._get_products_price(
            no_packs, quantity=quantity, uom=uom, date=date, **kwargs
        )
        for pack in packs:
            res[pack.id] = self._get_product_price(
                product=pack, quantity=quantity, uom=uom, date=date, **kwargs
            )
        return res
