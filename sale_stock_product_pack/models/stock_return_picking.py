###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    @api.onchange("product_return_moves")
    def _onchange_product_return_moves(self):
        for return_move in self.product_return_moves:
            if (
                return_move.product_id.pack_ok
                and return_move.product_id.detailed_type == "consu"
                and not return_move.move_id.sale_line_id.pack_parent_line_id
            ):
                pack_child_ids = return_move.product_id.pack_line_ids
                product_return_moves = self.product_return_moves.filtered(
                    lambda m: m.move_id.sale_line_id.pack_parent_line_id
                    == return_move.move_id.sale_line_id
                )
                for child in pack_child_ids:
                    child_product_return_move = product_return_moves.filtered(
                        lambda m: m.product_id == child.product_id
                    )[0]
                    if child_product_return_move:
                        child_product_return_move.quantity = (
                            return_move.quantity * child.quantity
                        )
