# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def copy(self, default=None):
        sale_copy = super().copy(default)
        # we unlink pack lines that should not be copied
        pack_copied_lines = sale_copy.order_line.filtered(
            lambda line: line.pack_parent_line_id.order_id == self
        )
        pack_copied_lines.with_context(pack_children_force_unlink=True).unlink()
        return sale_copy

    def write(self, vals):
        pack_parent_delete_ids = []
        if "order_line" in vals:
            to_delete_ids = [e[1] for e in vals["order_line"] if e[0] == 2]
            if to_delete_ids:
                pack_parent_delete_ids = (
                    self.env["sale.order.line"]
                    .browse(to_delete_ids)
                    .filtered(lambda line: line.pack_child_line_ids)
                    .ids
                )
            subpacks_to_delete_ids = (
                self.env["sale.order.line"]
                .search(
                    [("id", "child_of", to_delete_ids), ("id", "not in", to_delete_ids)]
                )
                .ids
            )
            if subpacks_to_delete_ids:
                for cmd in vals["order_line"]:
                    if cmd[1] in subpacks_to_delete_ids:
                        if cmd[0] != 2:
                            cmd[0] = 2
                        subpacks_to_delete_ids.remove(cmd[1])
                for to_delete_id in subpacks_to_delete_ids:
                    vals["order_line"].append([2, to_delete_id, False])
        if pack_parent_delete_ids:
            return super(
                SaleOrder,
                self.with_context(pack_parent_delete_ids=pack_parent_delete_ids),
            ).write(vals)
        return super().write(vals)

    def _get_update_prices_lines(self):
        res = super()._get_update_prices_lines()
        return res.filtered(
            lambda line: not line.pack_parent_line_id
            or line.pack_parent_line_id.pack_component_price == "detailed"
        )
