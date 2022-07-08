# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_quantities_dict(
        self, lot_id, owner_id, package_id, from_date=False, to_date=False
    ):
        res = super()._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date=from_date, to_date=to_date
        )
        packs = self.filtered("pack_ok")

        def pack_quantity(components):
            """ Returns the number of packs that can be assembled with the stock of
                the components.
                :param components: List of tuples (stock, quantity required for pack)
            """
            return (
                components
                and min(
                    [math.floor(stock / quantity) for stock, quantity in components]
                )
                or 0
            )

        for product in packs.with_context(prefetch_fields=False):
            sub_available = []
            sub_available_incoming = []
            sub_available_ongoing = []
            pack_free_qty = []
            subproducts = product.pack_line_ids.filtered(
                lambda p: p.product_id.type == "product"
            )
            for subproduct in subproducts.filtered(lambda s: s.quantity):
                subproduct_stock = subproduct.product_id
                sub_qty = subproduct.quantity
                s_qty_available = res.get(subproduct_stock.id, {}).get(
                    "qty_available", subproduct_stock.qty_available
                )
                s_incoming_qty = res.get(subproduct_stock.id, {}).get(
                    "incoming_qty", subproduct_stock.incoming_qty
                )
                s_outgoing_qty = res.get(subproduct_stock.id, {}).get(
                    "outgoing_qty", subproduct_stock.outgoing_qty
                )
                s_free_qty = res.get(subproduct_stock.id, {}).get(
                    "free_qty", subproduct_stock.free_qty
                )
                sub_available.append((s_qty_available, sub_qty))
                sub_available_incoming.append(
                    (s_qty_available + s_incoming_qty, sub_qty)
                )
                sub_available_ongoing.append(
                    (s_qty_available - s_outgoing_qty, sub_qty)
                )
                pack_free_qty.append((s_free_qty, sub_qty))

            # The number of packs that can be assembled with the stock on hand.
            pack_qty_available = pack_quantity(sub_available)
            # The number of extra packs that I will be able to assemble
            # if arrives the incoming stock.
            pack_incoming_qty = (
                pack_quantity(sub_available_incoming) - pack_qty_available
            )
            # The number of packs that I will NOT be able to assemble
            # if the outgoing stock is delivered.
            pack_outgoing_qty = pack_qty_available - pack_quantity(
                sub_available_ongoing
            )
            res[product.id] = {
                "qty_available": pack_qty_available,
                "incoming_qty": pack_incoming_qty,
                "outgoing_qty": pack_outgoing_qty,
                "virtual_available": pack_qty_available
                + pack_incoming_qty
                - pack_outgoing_qty,
                "free_qty": pack_quantity(pack_free_qty),
            }
        return res

    def _compute_quantities(self):
        """ In v13 Odoo introduces a filter for products not services.
        To keep how it was working on v12 we try to get stock for
        service products if they are pack.
        """
        service_pack_products = self.filtered(
            lambda p: p.type == "service" and p.pack_ok
        )
        super(ProductProduct, self - service_pack_products)._compute_quantities()
        res = service_pack_products._compute_quantities_dict(
            self._context.get("lot_id"),
            self._context.get("owner_id"),
            self._context.get("package_id"),
            self._context.get("from_date"),
            self._context.get("to_date"),
        )
        for product in service_pack_products:
            product.qty_available = res[product.id]["qty_available"]
            product.incoming_qty = res[product.id]["incoming_qty"]
            product.outgoing_qty = res[product.id]["outgoing_qty"]
            product.virtual_available = res[product.id]["virtual_available"]
            product.free_qty = res[product.id]["free_qty"]
