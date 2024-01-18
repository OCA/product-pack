# Copyright 2023 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def group_recordset_by(self, key):
        """Return a collection of pairs ``(key, recordset)`` from ``self``. The
        ``key`` is a function computing a key value for each element. This
        function is similar to ``itertools.groupby``, but aggregates all
        elements under the same key, not only consecutive elements.

        it's also similar to ``òdoo.tools.misc.groupby`` but return a recordset
        of sale.order.line instead list

        this let write some code likes this::

            my_recordset.filtered(
                lambda record: record.to_use
            ).group_recordset_by(
                lambda record: record.group_key
            )
        """
        groups = defaultdict(self.env[self._name].browse)
        for elem in self:
            groups[key(elem)] |= elem
        return groups.items()
