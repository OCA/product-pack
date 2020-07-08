# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class TestSaleProductPack(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls.env["sale.order"].create(
            {"partner_id": cls.env.ref("base.res_partner_12").id}
        )

    def _get_component_prices_sum(self, product_pack):
        component_prices = 0.0
        for pack_line in product_pack.get_pack_lines():
            product_line_price = pack_line.product_id.list_price * (
                1 - (pack_line.sale_discount or 0.0) / 100.0
            )
            component_prices += product_line_price * pack_line.quantity
        return component_prices

    def test_create_components_price_order_line(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.sale_order.order_line.mapped("product_id"),
            product_cp | product_cp.get_pack_lines().mapped("product_id"),
        )

    def test_create_ignored_price_order_line(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.sale_order.order_line.mapped("product_id"),
            product_tp | product_tp.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is different from the sum of component prices
        self.assertEqual(line.price_subtotal, 30.75)
        self.assertNotEqual(self._get_component_prices_sum(product_tp), 30.75)

    def test_create_totalized_price_order_line(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.sale_order.order_line.mapped("product_id"),
            product_tp | product_tp.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is equal to the sum of component prices
        self.assertEqual(line.price_subtotal, 2662.5)
        self.assertEqual(self._get_component_prices_sum(product_tp), 2662.5)

    def test_create_non_detailed_price_order_line(self):
        product_ndtp = self.env.ref("product_pack.product_pack_cpu_non_detailed")
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_ndtp.name,
                "product_id": product_ndtp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be only one line, because product_type is
        # not a detailed one
        self.assertEqual(self.sale_order.order_line, line)
        # Pack price is equal to the sum of component prices
        self.assertEqual(line.price_subtotal, 2662.5)
        self.assertEqual(self._get_component_prices_sum(product_ndtp), 2662.5)

    def test_update_qty(self):
        # Ensure the quantities are always updated

        def qty_in_order():
            return sum(self.sale_order.order_line.mapped("product_uom_qty"))

        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        main_sol = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        total_qty_init = qty_in_order()
        # change qty of main sol
        main_sol.product_uom_qty = 2 * main_sol.product_uom_qty
        total_qty_updated = qty_in_order()
        # Ensure all quantities have doubled
        self.assertEqual(total_qty_init * 2, total_qty_updated)

        # Confirm the sale
        self.sale_order.action_confirm()

        # Ensure we can still update the quantity
        main_sol.product_uom_qty = 2 * main_sol.product_uom_qty
        total_qty_confirmed = qty_in_order()
        self.assertEqual(total_qty_updated * 2, total_qty_confirmed)
