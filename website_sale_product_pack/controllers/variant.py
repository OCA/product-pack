# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request

from odoo.addons.sale.controllers.variant import VariantController


class WebsiteSaleVariantController(VariantController):
    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
            res = super().get_combination_info_website(product_template_id=product_template_id, product_id=product_id, combination=combination, add_qty=add_qty, **kw)
            combination = request.env['product.template.attribute.value'].browse(combination)
            product = request.env['product.template'].browse(product_template_id)
            product_pack_price = product.with_context(whole_pack_price=True)._get_combination_info(combination=combination, product_id=product_id, add_qty=add_qty or 1)
            if product.pack_ok and product.pack_component_price != 'ignored':
                  res['price'] = product_pack_price['price']
            return res
