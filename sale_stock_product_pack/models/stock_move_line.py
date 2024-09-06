# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    # TODO: Check if it is possible to remove it
    def _get_aggregated_product_quantities(self, **kwargs):
        """If any product pack has been used and is consumable we must reorder.
        Example of picking:
        - Consumable product (pack): sequence 10 (stock.move, id=1)
        - Storable product A: sequence 11 (stock.move, id=2)
        - Storable product B: sequence 12 (stock.move, id=3)
        Confirm picking (Storable products have stock) and we get the following:
        - stock.move.line, id=1, move_id=2 (Storable product A)
        - stock.move.line, id=2, move_id=3 (Storable product B)
        - stock.move.line, id=3, move_id=1 (Consumable product (pack))
        Done picking and print Delivery Slip report, this method is used to print table,
        and we get a confusing order, so we must reorder them according to the sequence
        of the linked stock.move.
        This is a known side effect in the stock addon when using consumable product +
        storable products but for now we only reorder for product packs.
        """
        if any(
            sml.move_id.sale_line_id
            and sml.product_id.pack_ok
            and sml.product_id.detailed_type == "consu"
            for sml in self
        ):
            ordered_self = self.env["stock.move.line"]
            for item in self:
                if item in ordered_self:
                    continue
                ppl = item.move_id.sale_line_id.pack_parent_line_id
                if (
                    ppl
                    and ppl.product_id.pack_ok
                    and ppl.product_id.detailed_type == "consu"
                ):
                    # First add sml from product pack
                    ordered_self += self.filtered(
                        lambda x: x.product_id == ppl.product_id
                    )
                    # After add sml records from pack_child_line_ids
                    for line in ppl.pack_child_line_ids:
                        ordered_self += self.filtered(
                            lambda x: x.product_id == line.product_id
                        )
                    continue
                ordered_self += item
            return super(
                StockMoveLine, ordered_self
            )._get_aggregated_product_quantities(**kwargs)
        return super()._get_aggregated_product_quantities(**kwargs)
