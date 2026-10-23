# Copyright 2026 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.website_sale.controllers.cart import Cart


class WebsiteSaleProductPackCart(Cart):
    def _get_cart_notification_information(self, order, added_qty_per_line):
        """Announce the price of the whole pack, not the one of its main line.

        The main line of a pack whose components carry the price is at 0, so
        the notification said the pack was free while the shop and the product
        page showed the price of the whole pack.
        """
        res = super()._get_cart_notification_information(order, added_qty_per_line)
        if not res.get("lines"):
            return res

        price_field = (
            "price_reduce_taxinc"
            if order.website_id.tax_display == "tax_included"
            else "price_reduce_taxexcl"
        )
        for values in res["lines"]:
            line = order.order_line.browse(values["id"])
            # Only the main line of a pack: a component is not announced on its own.
            if line._get_pack_root_line() != line or not line.product_uom_qty:
                continue
            pack_price = sum(
                pack_line[price_field] * pack_line.product_uom_qty
                for pack_line in line._get_pack_lines()
            )
            values["price_total"] = (
                pack_price / line.product_uom_qty * added_qty_per_line[line.id]
            )
        return res
