# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class Website(models.Model):
    _inherit = "website"

    def sale_get_order(
        self,
        force_create=False,
        code=None,
        update_pricelist=False,
        force_pricelist=False,
    ):
        """Communicate with product pack expansion method to check if it's necessary
        to expand the product pack lines or not via context"""
        if update_pricelist:
            return super(
                Website, self.with_context(update_pricelist=True)
            ).sale_get_order(force_create, code, update_pricelist, force_pricelist)
        return super().sale_get_order(
            force_create, code, update_pricelist, force_pricelist
        )
