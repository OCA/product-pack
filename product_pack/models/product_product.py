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
        """Split products and the pack in 2 separate recordsets.

        :return: [packs, no_packs]
        """
        packs = self.filtered(
            lambda p: p.pack_ok
            and (
                (p.pack_type == "detailed" and p.pack_component_price == "totalized")
                or p.pack_type == "non_detailed"
            )
        )
        # TODO: Check why this is needed
        # for compatibility with website_sale
        if self._context.get("website_id", False) and not self._context.get(
            "from_cart", False
        ):
            packs |= self.filtered(
                lambda p: p.pack_ok
                and p.pack_type == "detailed"
                and p.pack_component_price == "detailed"
            )

        return packs, (self - packs)

    def price_compute(self, price_type, uom=False, currency=False, company=False):
        packs, no_packs = self.split_pack_products()
        prices = super(ProductProduct, no_packs).price_compute(
            price_type, uom, currency, company
        )
        for product in packs.with_context(prefetch_fields=False):
            pack_price = 0.0
            for pack_line in product.sudo().pack_line_ids:
                pack_price += pack_line.get_price()
            pricelist_id_or_name = self._context.get("pricelist")
            # if there is a pricelist on the context the returned prices are on
            # that currency but, if the pack product has a different currency
            # it will be converted again by pp._compute_price_rule, so if
            # that is the case we convert the amounts to the pack currency
            if pricelist_id_or_name:
                if isinstance(pricelist_id_or_name, list):
                    pricelist_id_or_name = pricelist_id_or_name[0]
                if isinstance(pricelist_id_or_name, str):
                    pricelist_name_search = self.env["product.pricelist"].name_search(
                        pricelist_id_or_name, operator="=", limit=1
                    )
                    if pricelist_name_search:
                        pricelist = self.env["product.pricelist"].browse(
                            [pricelist_name_search[0][0]]
                        )
                elif isinstance(pricelist_id_or_name, int):
                    pricelist = self.env["product.pricelist"].browse(
                        pricelist_id_or_name
                    )
                if pricelist and pricelist.currency_id != product.currency_id:
                    pack_price = pricelist.currency_id._convert(
                        pack_price,
                        product.currency_id,
                        self.company_id or self.env.company,
                        fields.Date.today(),
                    )
            prices[product.id] = pack_price
        return prices

    @api.depends("list_price", "price_extra")
    def _compute_product_lst_price(self):
        packs, no_packs = self.split_pack_products()
        super(ProductProduct, no_packs)._compute_product_lst_price()
        to_uom = None
        if "uom" in self._context:
            to_uom = self.env["uom.uom"].browse([self._context["uom"]])
        for product in packs:
            list_price = product.price_compute("list_price").get(product.id)
            if to_uom:
                list_price = product.uom_id._compute_price(list_price, to_uom)
            product.lst_price = list_price + product.price_extra
