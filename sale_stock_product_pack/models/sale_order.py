# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=W8110
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_qty_delivered(self):
        """Compute pack delivered pack quantites according to its components
        deliveries"""
        super()._compute_qty_delivered()
        main_pack_lines = self.filtered("pack_parent_line_id").mapped(
            "pack_parent_line_id"
        )
        for line in main_pack_lines.filtered(
            lambda x: x.qty_delivered_method == "stock_move"
            and x.pack_child_line_ids
            and x.product_uom_qty
        ):
            delivered_packs = []
            # We filter non qty lines of editable packs
            for pack_line in line.pack_child_line_ids.filtered("product_uom_qty"):
                # If a component isn't delivered, the pack isn't as well
                if not pack_line.qty_delivered:
                    delivered_packs.append(0)
                    break
                qty_per_pack = pack_line.product_uom_qty / line.product_uom_qty
                delivered_packs.append(pack_line.qty_delivered / qty_per_pack)
            line.qty_delivered = delivered_packs and min(delivered_packs) or 0.0
