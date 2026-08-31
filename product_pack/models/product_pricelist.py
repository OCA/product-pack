from odoo import models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_product_price(self, product, *args, **kwargs):
        """Compute the pricelist price for the specified pack product, qty & uom.

        :returns: unit price of the pack product + components,
                  considering pricelist rules
        """
        self and self.ensure_one()
        if product._is_pack_to_be_handled() and not self.env.context.get(
            "pack_base_price_only"
        ):
            # NOTE: This exception is to avoid adding the list price of the packs
            # "totalized" and "non detailed". Should be removed to solve the issue #169.
            if (
                product.pack_type == "non_detailed"
                or product.pack_component_price == "totalized"
            ):
                pack_price = 0
            else:
                # A rule based on another pricelist resolves through this same
                # method, so ask for the pack's own price to avoid totalizing twice.
                pack_price = self.with_context(
                    pack_base_price_only=True
                )._compute_price_rule(product, *args, **kwargs)[product.id][0]

            for line in product.sudo().pack_line_ids:
                pack_price += line._get_pack_line_price(self, *args, **kwargs)
            return pack_price
        else:
            return super()._get_product_price(product, *args, **kwargs)

    def _get_product_price_rule(self, product, *args, **kwargs):
        """Compute the pricelist price & rule for the specified pack product.

        The pack price is built from its components, so the bare pricelist rule
        price is not the pack price. The e-commerce product page and shop listing
        (`website_sale`) and the product configurator reach the price through this
        method, not through `_get_product_price`.

        No single rule explains a pack price, so none is reported: applying the
        returned rule to the pack alone yields an unrelated price, which the shop
        would render as a discount that does not exist.

        :returns: (unit price of the pack product + components, False)
        """
        self and self.ensure_one()
        if product._is_pack_to_be_handled() and not self.env.context.get(
            "pack_base_price_only"
        ):
            return self._get_product_price(product, *args, **kwargs), False
        return super()._get_product_price_rule(product, *args, **kwargs)

    def _get_products_price(self, products, *args, **kwargs):
        """Compute the pricelist price for the specified pack product, qty & uom.

        :returns: unit price of the pack product + components,
                  considering pricelist rules
        """
        packs, no_packs = products.split_pack_products()
        res = super()._get_products_price(no_packs, *args, **kwargs)
        for pack in packs:
            res[pack.id] = self._get_product_price(pack, *args, **kwargs)
        return res
