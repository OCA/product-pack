from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("pack_type", "pack_component_price")
    def _check_contract_component(self):
        for product in self:
            if product.pack_ok:
                product.pack_line_ids._check_contract_component()
