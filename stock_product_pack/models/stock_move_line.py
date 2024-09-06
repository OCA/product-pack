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
            sml.product_id.pack_ok and sml.product_id.detailed_type == "consu"
            for sml in self
        ):
            self = self.sorted(key=lambda x: x.move_id.sequence)
        return super()._get_aggregated_product_quantities(**kwargs)
