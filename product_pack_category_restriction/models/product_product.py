# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.onchange("categ_id")
    def _onchange_categ_id(self):
        res = super()._onchange_categ_id()
        if self.categ_id:
            self.pack_ok = self.categ_id.pack_ok
        return res

    @api.onchange("pack_ok")
    def _onchange_pack_ok(self):
        if self.pack_ok:
            return {"domain": {"categ_id": [("pack_ok", "=", True)]}}
        else:
            return {"domain": {"categ_id": []}}
