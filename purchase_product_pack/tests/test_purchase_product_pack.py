# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import TransactionCase

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestPurchaseProductPack(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
            }
        )

    def _get_component_costs_sum(self, product_pack):
        component_prices = 0.0
        for pack_line in product_pack.get_pack_lines():
            product_line_price = pack_line.product_id.standard_price
            component_prices += product_line_price * pack_line.quantity
        return component_prices

    def test_create_components_cost_order_line(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 4)
        pack_line = self.purchase_order.order_line.filtered(
            lambda pline: pline.product_id == product_cp
        )
        # Check if sequence is the same as pack product one
        sequence = pack_line.sequence
        self.assertEqual(
            [sequence, sequence, sequence, sequence],
            self.purchase_order.order_line.mapped("sequence"),
        )
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.purchase_order.order_line.mapped("product_id"),
            product_cp | product_cp.get_pack_lines().mapped("product_id"),
        )
        # Check the subtotal on lines
        self.assertAlmostEqual(line.price_subtotal, 20.5)
        self.assertEqual(
            (self.purchase_order.order_line - line).mapped("price_subtotal"),
            [1700.0, 20.0, 876.0],
        )

    def test_create_ignored_cost_order_line(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.purchase_order.order_line.mapped("product_id"),
            product_tp | product_tp.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual(
            (self.purchase_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is different from the sum of component prices
        self.assertAlmostEqual(line.price_subtotal, 20.5)
        self.assertNotEqual(self._get_component_costs_sum(product_tp), 20.5)

    def test_create_totalized_cost_order_line(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.purchase_order.order_line.mapped("product_id"),
            product_tp | product_tp.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertAlmostEqual(
            (self.purchase_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is equal to the sum of component prices
        self.assertAlmostEqual(line.price_subtotal, 2596.0)
        self.assertAlmostEqual(self._get_component_costs_sum(product_tp), 2596.0)

    def test_create_non_detailed_price_order_line(self):
        product_ndtp = self.env.ref("product_pack.product_pack_cpu_non_detailed")
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_ndtp.name,
                "product_id": product_ndtp.id,
                "product_qty": 1,
            }
        )
        # After create, there will be only one line, because product_type is
        # not a detailed one
        self.assertEqual(self.purchase_order.order_line, line)
        # Pack price is equal to the sum of component prices
        self.assertAlmostEqual(line.price_subtotal, 2596.0)
        self.assertAlmostEqual(self._get_component_costs_sum(product_ndtp), 2596.0)

    def test_update_qty(self):
        # Ensure the quantities are always updated

        def qty_in_order():
            return sum(self.purchase_order.order_line.mapped("product_qty"))

        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        main_sol = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_qty": 1,
            }
        )
        total_qty_init = qty_in_order()
        # change qty of main sol
        main_sol.product_qty = 2 * main_sol.product_qty
        total_qty_updated = qty_in_order()
        # Ensure all quantities have doubled
        self.assertAlmostEqual(total_qty_init * 2, total_qty_updated)

        # Confirm the purchase
        self.purchase_order.button_confirm()

        # Ensure we can still update the quantity
        main_sol.product_qty = 2 * main_sol.product_qty
        total_qty_confirmed = qty_in_order()
        self.assertAlmostEqual(total_qty_updated * 2, total_qty_confirmed)

    def test_do_not_expand(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        pack_line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 4)
        pack_line_update = pack_line.with_context(update_prices=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)
        pack_line_update = pack_line.with_context(update_pricelist=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)

    def test_create_several_lines(self):
        # Create two purchase order lines with two pack products
        # Check 8 lines are created
        # Check lines sequences and order are respected
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        vals = [
            {
                "order_id": self.purchase_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_qty": 1,
            },
            {
                "order_id": self.purchase_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_qty": 1,
            },
        ]
        self.env["purchase.order.line"].create(vals)
        # After create, there will be eight lines (4 + 4)
        self.assertEqual(len(self.purchase_order.order_line), 8)
        # Check if lines are well ordered
        self.assertEqual(self.purchase_order.order_line[0].product_id, product_cp)
        sequence_cp = self.purchase_order.order_line[0].sequence
        self.assertEqual(sequence_cp, self.purchase_order.order_line[1].sequence)
        self.assertEqual(sequence_cp, self.purchase_order.order_line[2].sequence)
        self.assertEqual(sequence_cp, self.purchase_order.order_line[3].sequence)

        self.assertEqual(self.purchase_order.order_line[4].product_id, product_tp)
        sequence_tp = self.purchase_order.order_line[4].sequence
        self.assertEqual(sequence_tp, self.purchase_order.order_line[5].sequence)
        self.assertEqual(sequence_tp, self.purchase_order.order_line[6].sequence)
        self.assertEqual(sequence_tp, self.purchase_order.order_line[7].sequence)

    def test_order_line_detailed_with_seller(self):
        # Check with detailed options
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        product_cp.write(
            {
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.env.ref("base.res_partner_12").id,
                            "min_qty": 1.0,
                            "price": 25.0,
                        },
                    )
                ]
            }
        )
        product_product_16 = self.env.ref("product.product_product_16")
        product_product_16.write(
            {
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.env.ref("base.res_partner_12").id,
                            "min_qty": 1.0,
                            "price": 15.0,
                        },
                    )
                ]
            }
        )
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_qty": 1,
            }
        )
        # Check the subtotal corresponding to seller on lines
        self.assertAlmostEqual(line.price_subtotal, 25.0)
        self.assertEqual(
            (self.purchase_order.order_line - line).mapped("price_subtotal"),
            [1700.0, 15.0, 876.0],
        )

    def test_order_line_totalized_with_seller(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        product_product_16 = self.env.ref("product.product_product_16")
        product_product_16.write(
            {
                "seller_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": self.env.ref("base.res_partner_12").id,
                            "min_qty": 1.0,
                            "price": 15.0,
                        },
                    )
                ]
            }
        )
        line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_qty": 1,
            }
        )
        # Check the subtotal corresponding to seller on lines
        self.assertAlmostEqual(line.price_subtotal, 2591.0)
        self.assertAlmostEqual(
            (self.purchase_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )

    def test_get_seller_cost_no_line(self):
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        # Consult the price of the product without a purchase order line
        prices = product_tp.pack_cost_compute(False)
        cost = prices[product_tp.id]
        self.assertEqual(cost, 2596.0)
        # standard_price (20.5) * quantity (126.63414634146341463414634146341)
