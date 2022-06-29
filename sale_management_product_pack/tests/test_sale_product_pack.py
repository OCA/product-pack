# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase
from odoo.tests.common import Form


class TestSaleManagementProductPack(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "currency_id": cls.env.user.company_id.currency_id.id,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo",
                "property_product_pricelist": cls.pricelist.id,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )

    def _get_component_prices_sum(self, product_pack):
        component_prices = 0.0
        for pack_line in product_pack.get_pack_lines():
            product_line_price = pack_line.product_id.list_price * (
                1 - (pack_line.sale_discount or 0.0) / 100.0
            )
            component_prices += product_line_price * pack_line.quantity
        return component_prices

    def test_create_order_line_order_from_sale_order_template(self):
        sale_order_template = self.env["sale.order.template"].create(
            {"name": "Test pack SO template", "number_of_days": 15}
        )
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        self.env["sale.order.template.line"].create(
            [
                {
                    "sale_order_template_id": sale_order_template.id,
                    "product_id": product_tp.id,
                    "name": product_tp.name,
                    "product_uom_qty": 3,
                    "product_uom_id": self.env.ref("uom.product_uom_unit").id,
                    "price_unit": product_tp.list_price,
                    # "discount":, # >10.00</field>
                }
            ]
        )
        with Form(self.sale_order) as form:
            form.sale_order_template_id = sale_order_template
            sale_order = form.save()
        # After create, there will be four lines
        self.assertEqual(len(sale_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        line = sale_order.order_line.filtered(lambda l: l.product_id == product_tp)
        self.assertEqual(
            sale_order.order_line.mapped("product_id"),
            product_tp | product_tp.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual(
            (sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is equal to the sum of component prices
        self.assertEqual(line.price_subtotal, 2662.5 * 3)
        self.assertEqual(self._get_component_prices_sum(product_tp), 2662.5)
