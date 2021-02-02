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
        for product in packs.with_context(prefetch_fields=False):
            pack_qty_available = []
            pack_virtual_available = []
            pack_free_qty = []
            subproducts = product.pack_line_ids.filtered(
                lambda p: p.product_id.type == "product"
            )
            for subproduct in subproducts:
                subproduct_stock = subproduct.product_id
                sub_qty = subproduct.quantity
                if sub_qty:
                    pack_qty_available.append(
                        math.floor(subproduct_stock.qty_available / sub_qty)
                    )
                    pack_virtual_available.append(
                        math.floor(subproduct_stock.virtual_available / sub_qty)
                    )
                    pack_free_qty.append(
                        math.floor(subproduct_stock.free_qty / sub_qty)
                    )
            res[product.id] = {
                "qty_available": (pack_qty_available and min(pack_qty_available) or 0),
                "free_qty": (pack_free_qty and min(pack_free_qty) or 0),
                "incoming_qty": 0,
                "outgoing_qty": 0,
                "virtual_available": (
                    pack_virtual_available and min(pack_virtual_available) or 0
                ),
            }
        return res
