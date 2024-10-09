##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class SaleOrderLinePackLine(models.Model):
    _name = "sale.order.line.pack.line"
    _description = "Sale Order None Detailed Pack Lines"

    order_line_id = fields.Many2one(
        "sale.order.line", "Order Line", ondelete="cascade", index=True, required=True
    )
    product_id = fields.Many2one("product.product", "Product", required=True)
    price_unit = fields.Float("Unit Price", required=True, digits="Product Price")
    discount = fields.Float(
        "Discount (%)",
        digits="Discount",
    )
    price_subtotal = fields.Float(
        compute="_compute_price_subtotal", string="Subtotal", digits="Account"
    )
    product_uom_qty = fields.Float("Quantity", digits="Product UoS", required=True)
    currency_id = fields.Many2one(
        string="Currency", related="order_line_id.currency_id"
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        for line in self:
            line.price_unit = (
                line.product_id._get_contextual_price() if line.product_id else 0.0
            )

    @api.depends("price_unit", "product_uom_qty")
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = (
                line.product_uom_qty
                * line.price_unit
                * (1 - (line.discount or 0.0) / 100.0)
            )
