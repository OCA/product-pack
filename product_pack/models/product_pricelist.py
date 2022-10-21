# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from itertools import chain

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """Don't call super when dealing with detailed and non detailed packs,
        as the computations done after calling `price_compute` modify the final returned
        price, so we compute it directly in these cases.
        """

        if not date:
            date = self._context.get("date") or fields.Datetime.now()
        if not uom_id and self._context.get("uom"):
            uom_id = self._context["uom"]
        if uom_id:
            # rebrowse with uom if given
            products = [
                item[0].with_context(uom=uom_id) for item in products_qty_partner
            ]
            products_qty_partner = [
                (products[index], data_struct[1], data_struct[2])
                for index, data_struct in enumerate(products_qty_partner)
            ]
        else:
            products = [item[0] for item in products_qty_partner]
        if not products:
            return {}
        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = list(categ_ids)
        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [
                p.id
                for p in list(
                    chain.from_iterable([t.product_variant_ids for t in products])
                )
            ]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        items = self._compute_price_rule_get_items(
            products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids
        )
        for rule in items:
            if rule.base == "pricelist" and rule.base_pricelist_id:
                return super()._compute_price_rule(
                    products_qty_partner, date=date, uom_id=uom_id
                )

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
