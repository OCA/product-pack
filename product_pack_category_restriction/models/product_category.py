# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    pack_ok = fields.Boolean(string="Is Pack Category?", default=True)

    @api.constrains("pack_ok")
    def _check_pack_ok(self):
        """Check pack products are only on pack categories"""
        categs = self.filtered(lambda c: not c.pack_ok)
        if categs:
            products = self.env["product.template"].search(
                [("categ_id", "in", categs.ids), ("pack_ok", "=", True)]
            )
            if products:
                raise ValidationError(
                    _("Non-pack Category can't contain pack products.")
                )
