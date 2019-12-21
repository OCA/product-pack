# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def copy(self, default=None):
        sale_copy = super().copy(default)
        # we unlink pack lines that should not be copied
        pack_copied_lines = sale_copy.order_line.filtered(
            lambda l: l.pack_parent_line_id.order_id == self
        )
        pack_copied_lines.unlink()
        return sale_copy

    @api.onchange("order_line")
    def check_pack_line_unlink(self):
        """At least on embeded tree editable view odoo returns a recordset on
        _origin.order_line only when lines are unlinked and this is exactly
        what we need
        """

        # New order case, ignoring
        if len(self.order_line) == 0:
            return

        # Add a new line case, ignoring
        if len(self.order_line) > len(self._origin.order_line):
            return

        # Get the deleted line
        origin = []
        news = []
        for x in self._origin.order_line:
            origin.append(x)
            for y in self.order_line:
                if x.id == y._ids[0].origin:
                    news.append(x)

        diff = list(set(origin) - set(news))

        line_is_pack = False
        if diff:
            if diff[0]:
                line_is_pack = diff[0].product_id.pack_ok

                if line_is_pack:
                    # Also delete all children lines
                    lines_to_delete = []
                    children = diff[0].mapped("pack_child_line_ids")
                    for child in children:
                        lines_to_delete.append([2, child.id, 0])

                        # In case of a pack in a pack, delete also the childen of the children
                        for child2 in child.mapped("pack_child_line_ids"):
                            lines_to_delete.append([2, child2.id, 0])

                    self.update({'order_line': lines_to_delete })

                else:

                    # This is a subline
                    if (
                            diff[0].pack_parent_line_id and
                            not diff[0].pack_parent_line_id.product_id.pack_modifiable
                    ):

                        raise UserError(
                            _(
                                "You can not delete this line because is part of a pack in"
                                " this sale order. In order to delete this line you need to"
                                " delete the pack itself"
                            )
                        )            
