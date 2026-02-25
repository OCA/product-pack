# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange("quantity_done")
    def _onchange_quantity_done(self):
        if self.sale_line_id.pack_parent_line_id:
            self.quantity_done = self._origin.quantity_done
            raise UserError(
                _(
                    "You can not change this line because is part of a pack"
                    " included in this picking."
                )
            )
        if (
            self.product_id.pack_ok
            and self.product_id.detailed_type == "consu"
            and not self.sale_line_id.pack_parent_line_id
        ):
            pack_child_ids = self.product_id.pack_line_ids
            move_ids = self.picking_id._origin.move_ids.filtered(
                lambda m: m.sale_line_id.pack_parent_line_id == self.sale_line_id
            )
            for child in pack_child_ids:
                child_move = move_ids.filtered(
                    lambda m: m.product_id == child.product_id
                )[0]
                if child_move:
                    child_move.quantity_done = self.quantity_done * child.quantity
