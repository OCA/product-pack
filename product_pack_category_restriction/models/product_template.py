# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.constrains("pack_ok")
    def _check_pack_ok(self):
        products = self.filtered(lambda p: p.pack_ok)
        if products and any(not p.categ_id.pack_ok for p in products):
            raise ValidationError(_("Pack Products must be part of a Pack Category."))

    @api.onchange("categ_id")
    def _onchange_categ_id(self):
        if self.categ_id:
            self.pack_ok = self.categ_id.pack_ok

    @api.onchange("pack_ok")
    def _onchange_pack_ok(self):
        if self.pack_ok:
            return {"domain": {"categ_id": [("pack_ok", "=", True)]}}
        else:
            return {"domain": {"categ_id": []}}
