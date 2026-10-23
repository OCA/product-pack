# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_properties(self, move_line=False, move=False):
        # It is important to set a specific line_key if any of the lines are linked to
        # a sale and are part of a pack, to prevent the data from being added to any
        # additional lines that order may have for that product
        result = super()._get_aggregated_properties(move_line, move)
        move = result["move"]
        if move.sale_line_id and move.sale_line_id.pack_parent_line_id:
            result["line_key"] += f"_{move.sale_line_id.pack_parent_line_id.id}"
        return result
