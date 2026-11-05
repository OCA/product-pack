# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("is_published")
    def check_website_published(self):
        """For keep the consistent and prevent bugs within the e-commerce,
        we force that all childs of a parent pack
        stay publish when the parent is published.
        Also if any of the childs of the parent pack became unpublish,
        we unpublish the parent."""
        for rec in self.filtered(lambda x: x.pack_ok and x.is_published):
            unpublished = rec.pack_line_ids.mapped("product_id").filtered(
                lambda p: not p.is_published
            )
            if unpublished:
                raise ValidationError(
                    self.env._(
                        "You can't unpublished products (%(unpublished_products)s) "
                        "to a published pack (%(pack_name)s)",
                        unpublished_products=", ".join(unpublished.mapped("name")),
                        pack_name=rec.name,
                    )
                )

        for rec in self.filtered(
            lambda x: not x.is_published and x.used_in_pack_line_ids
        ):
            published = rec.used_in_pack_line_ids.mapped("parent_product_id").filtered(
                "is_published"
            )
            if published:
                raise ValidationError(
                    self.env._(
                        "You can't unpublished product (%(product_name)s) for a "
                        "published pack parents (%(pack_parents)s)",
                        product_name=rec.name,
                        pack_parents=", ".join(published.mapped("name")),
                    )
                )

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        uom_id=False,
        only_template=False,
    ):
        """Override to add the information about packs with whole_pack_price context"""
        return super(
            ProductTemplate, self.with_context(whole_pack_price=True)
        )._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
        )

    def _get_additionnal_combination_info(
        self, product_or_template, quantity, uom, date, website
    ):
        """Override to add the information about packs with whole_pack_price context"""
        res = super()._get_additionnal_combination_info(
            product_or_template, quantity, uom, date, website
        )

        if product_or_template.pack_ok:
            pricelist = request.pricelist
            currency = website.currency_id
            # _get_product_price is the one product_pack overrides to add up the
            # components; _get_product_price_rule goes straight to the core.
            pricelist_price = pricelist.with_context(
                whole_pack_price=True
            )._get_product_price(
                product_or_template,
                quantity,
                uom=uom,
                date=date,
                currency=currency,
            )

            # Apply taxes
            product_taxes = (
                product_or_template.sudo().taxes_id._filter_taxes_by_company(
                    self.env.company
                )
            )
            taxes = self.env["account.tax"]
            if product_taxes:
                taxes = request.fiscal_position.map_tax(product_taxes)
                res["price"] = self._apply_taxes_to_price(
                    pricelist_price,
                    currency,
                    product_taxes,
                    taxes,
                    product_or_template,
                    website=website,
                )
            else:
                res["price"] = pricelist_price
            # The core flags the pack with the price of its main product.
            res["prevent_zero_price_sale"] = (
                website.prevent_zero_price_sale
                and float_is_zero(res["price"], precision_rounding=currency.rounding)
            )

        return res

    def _website_show_quick_add(self):
        """Judge a pack by its whole price, not by the one of its main product"""
        return super(
            ProductTemplate, self.with_context(whole_pack_price=True)
        )._website_show_quick_add()

    def _get_sales_prices(self, website):
        """Override to add the price of the pack itself"""
        packs, no_packs = self.with_context(whole_pack_price=True).split_pack_products()
        prices = super(ProductTemplate, no_packs)._get_sales_prices(website)
        if packs:
            pricelist = request.pricelist
            currency = website.currency_id
            fiscal_position_sudo = request.fiscal_position
            date = fields.Date.context_today(self)

            for pack in packs:
                # _get_product_price is the one product_pack overrides to add up the
                # components; _get_product_price_rule goes straight to the core.
                pricelist_price = pricelist.with_context(
                    whole_pack_price=True
                )._get_product_price(
                    pack,
                    1.0,
                    uom=pack.uom_id,
                    date=date,
                    currency=currency,
                )

                # Apply taxes
                product_taxes = pack.sudo().taxes_id._filter_taxes_by_company(
                    self.env.company
                )
                taxes = self.env["account.tax"]
                if product_taxes:
                    taxes = fiscal_position_sudo.map_tax(product_taxes)
                    price_reduce = self._apply_taxes_to_price(
                        pricelist_price,
                        currency,
                        product_taxes,
                        taxes,
                        pack,
                        website=website,
                    )
                else:
                    price_reduce = pricelist_price

                prices[pack.id] = {"price_reduce": price_reduce}
        return prices
