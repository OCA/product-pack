# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    pack_line_ids = fields.One2many(
        "product.pack.line",
        "parent_product_id",
        "Pack Products",
        help="Products that are part of this pack.",
    )
    used_in_pack_line_ids = fields.One2many(
        "product.pack.line",
        "product_id",
        "Found in packs",
        help="Packs where product is used.",
    )

    def get_pack_lines(self):
        """Returns the content (lines) of the packs.
        By default, return all the pack_line_ids, but that function
        can be overloaded to introduce filtering function by date, etc..."""
        return self.mapped("pack_line_ids")

    def split_pack_products(self):
        packs = self.filtered(lambda p: p.product_tmpl_id._is_pack_to_be_handled())
        return packs, (self - packs)

    def price_compute(
        self, price_type, uom=False, currency=False, company=False, date=False
    ):
        packs, no_packs = self.split_pack_products()
        prices = super(ProductProduct, no_packs).price_compute(
            price_type, uom, currency, company, date
        )
        for product in packs.with_context(prefetch_fields=False):
            pack_price = 0.0
            if product.product_tmpl_id.pack_component_price == "detailed":
                pack_price = product.list_price
            pack_line_prices = product.sudo().pack_line_ids.price_compute(
                price_type, uom, currency, company, date
            )
            prices[product.id] = pack_price + sum(pack_line_prices.values())

        return prices

    @api.depends("list_price", "price_extra")
    def _compute_product_lst_price(self):
        packs, no_packs = self.split_pack_products()
        ret_val = super(ProductProduct, no_packs)._compute_product_lst_price()
        to_uom = None
        if "uom" in self._context:
            to_uom = self.env["uom.uom"].browse([self._context["uom"]])
        for product in packs:
            list_price = product.price_compute("list_price").get(product.id)
            if to_uom:
                list_price = product.uom_id._compute_price(list_price, to_uom)
            product.lst_price = list_price + product.price_extra
        return ret_val


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products, qty, uom=None, date=False, **kwargs):
        self.ensure_one()

        packs, no_packs = products.split_pack_products()
        res = super()._compute_price_rule(no_packs, qty, uom=uom, date=date, **kwargs)

        for pack in packs:
            pack_price = 0.0
            if pack.pack_component_price == "detailed":
                pack_price = pack.list_price
            pack_lines = pack.sudo().pack_line_ids
            tmp_products = pack_lines.mapped("product_id")
            tmp_res = super()._compute_price_rule(
                tmp_products, qty, uom=uom, date=date, **kwargs
            )
            for line in pack_lines:
                pack_price += tmp_res[line.product_id.id][0] * line.quantity
            res |= dict({pack.id: (pack_price, 0)})
        return res
