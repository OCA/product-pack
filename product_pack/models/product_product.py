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

    def _is_pack_to_be_handled(self):
        return self.product_tmpl_id._is_pack_to_be_handled()

    def split_pack_products(self):
        packs = self.filtered(lambda p: p.product_tmpl_id._is_pack_to_be_handled())
        return packs, (self - packs)

    @api.depends("list_price", "price_extra")
    def _compute_product_lst_price(self):
        packs, no_packs = self.with_context(whole_pack_price=True).split_pack_products()
        ret_val = super(ProductProduct, no_packs)._compute_product_lst_price()
        uom = self._context.get("uom", False)
        if uom:
            uom = self.env["uom.uom"].browse([uom])
        for product in packs:
            # NOTE: This exception is to avoid adding the list price of the packs
            # "totalized" and "non detailed". Should be removed to solve the issue #169.
            if (
                product.pack_type == "non_detailed"
                or product.pack_component_price == "totalized"
            ):
                list_price = 0
            else:
                list_price = product._price_compute("list_price", uom=uom).get(
                    product.id
                )
            list_price += sum(
                product.pack_line_ids._pack_line_price_compute(
                    "list_price", uom=uom
                ).values()
            )
            product.lst_price = list_price + product.price_extra
        return ret_val
