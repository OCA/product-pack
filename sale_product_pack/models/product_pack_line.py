# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class ProductPack(models.Model):
    _inherit = 'product.pack.line'

    sale_discount = fields.Float(
        'Sale discount (%)',
        digits=dp.get_precision('sale_discount'),
    )

    @api.multi
    def get_sale_order_line_vals(self, line, order):
        self.ensure_one()
        quantity = self.quantity * line.product_uom_qty
        line_vals = {
            'order_id': order.id,
            'product_id': self.product_id.id or False,
            'pack_parent_line_id': line.id,
            'pack_depth': line.pack_depth + 1,
            'company_id': order.company_id.id,
            'pack_modifiable': line.product_id.pack_modifiable,
        }
        sol = line.new(line_vals)
        sol.product_id_change()
        sol.product_uom_qty = quantity
        sol.product_uom_change()
        sol._onchange_discount()
        vals = sol._convert_to_write(sol._cache)
        pack_price_types = {'totalized', 'ignored'}
        sale_discount = 0.0
        if (line.product_id.pack_component_price == 'detailed'):
            sale_discount = 100.0 - (
                (100.0 - sol.discount) * (100.0 - self.sale_discount) / 100.0)
        elif (line.product_id.pack_type == 'detailed'
                and line.product_id.pack_component_price in pack_price_types):
            vals['price_unit'] = 0.0
        vals.update({
            'discount': sale_discount,
            'name': '%s%s' % (
                '> ' * (line.pack_depth + 1), sol.name
            ),
        })
        return vals

    @api.multi
    def get_price(self):
        self.ensure_one()
        return super().get_price() * (1 - self.sale_discount / 100.0)
