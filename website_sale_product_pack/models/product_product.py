# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("pack_line_ids")
    def check_website_published(self):
        for rec in self.filtered("is_published"):
            unpublished = rec.pack_line_ids.mapped("product_id").filtered(
                lambda x: not x.is_published
            )
            if unpublished:
                raise ValidationError(
                    _(
                        "You can't add unpublished products (%(unpublished_products)s) to"
                        "a published pack (%(pack_name)s)"
                    )
                    % {
                        "unpublished_products": ", ".join(unpublished.mapped("name")),
                        "pack_name": rec.name,
                    }
                )

    def _compute_quantities_dict(
        self, lot_id, owner_id, package_id, from_date=False, to_date=False
    ):
        packs = self.filtered("pack_ok")
        subproducts = packs.pack_line_ids.filtered(
            lambda p: p.product_id.detailed_type == "product"
        ).mapped("product_id")
        res = super(ProductProduct, self | subproducts)._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date=from_date, to_date=to_date
        )
        for pack in packs.with_context(prefetch_fields=False):
            pack_qty_available = []
            pack_virtual_available = []
            pack_free_qty = []

            for line in pack.pack_line_ids.filtered(
                lambda p: p.product_id.detailed_type == "product"
            ):
                sub_qty = line.quantity
                if sub_qty:
                    pack_qty_available.append(
                        math.floor(res[line.product_id.id]["qty_available"] / sub_qty)
                    )
                    pack_virtual_available.append(
                        math.floor(
                            res[line.product_id.id]["virtual_available"] / sub_qty
                        )
                    )
                    pack_free_qty.append(
                        math.floor(res[line.product_id.id]["free_qty"] / sub_qty)
                    )
            res[pack.id] = {
                "qty_available": (pack_qty_available and min(pack_qty_available) or 0),
                "free_qty": (pack_free_qty and min(pack_free_qty) or 0),
                "incoming_qty": 0,
                "outgoing_qty": 0,
                "virtual_available": (
                    pack_virtual_available and min(pack_virtual_available) or 0
                ),
            }
        return res
