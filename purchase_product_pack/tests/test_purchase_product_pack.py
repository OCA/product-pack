# Copyright 2023 Camptocamp SA
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo import Command

from .common import TestPurchaseProductPackBase


class TestPurchaseProductPack(TestPurchaseProductPackBase):
    def test_create_components_cost_order_line(self):
        self._add_po_line()
        # After create, there will be three lines
        self.assertEqual(len(self.purchase_order.order_line), 3)
        # Check if sequence is the same as pack product one
        for po_line in self.purchase_order.order_line:
            self.assertEqual(po_line.sequence, 10)
        # The products of those lines are the main product pack and its components
        self.assertEqual(self.purchase_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.purchase_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.purchase_order.order_line[2].product_id, self.component2)
        # Check the subtotal on lines
        self.assertEqual(self.purchase_order.order_line[0].price_subtotal, 5)
        self.assertEqual(self.purchase_order.order_line[1].price_subtotal, 24)
        self.assertEqual(self.purchase_order.order_line[2].price_subtotal, 18)

    def test_create_ignored_cost_order_line(self):
        self.pack.pack_component_price = "ignored"
        self._add_po_line()
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 3)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(self.purchase_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.purchase_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.purchase_order.order_line[2].product_id, self.component2)
        # All component lines have zero as subtotal
        self.assertEqual(self.purchase_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.purchase_order.order_line[2].price_subtotal, 0)
        # Pack price is different from the sum of component prices
        self.assertEqual(self.purchase_order.order_line[0].price_subtotal, 5)

    def test_create_totalized_cost_order_line(self):
        self.pack.pack_component_price = "totalized"
        self._add_po_line()
        # After create, there will be four lines
        self.assertEqual(len(self.purchase_order.order_line), 3)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(self.purchase_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.purchase_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.purchase_order.order_line[2].product_id, self.component2)
        # All component lines have zero as subtotal
        self.assertEqual(self.purchase_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.purchase_order.order_line[2].price_subtotal, 0)
        # Pack price is equal to the sum of component prices
        self.assertEqual(self.purchase_order.order_line[0].price_subtotal, 42)

    def test_create_non_detailed_price_order_line(self):
        self.pack.pack_type = "non_detailed"
        self._add_po_line()
        # After create, there will be only one line, because product_type is
        # not a detailed one
        self.assertEqual(len(self.purchase_order.order_line), 1)
        # Pack price is equal to the sum of component prices
        self.assertEqual(self.purchase_order.order_line.price_subtotal, 42)

    def test_update_qty(self):
        pack_line = self._add_po_line()
        # change qty of main sol and ensure all the quantities have doubled
        pack_line.product_qty = 2
        self.assertAlmostEqual(self.purchase_order.order_line[1].product_qty, 4)
        self.assertAlmostEqual(self.purchase_order.order_line[2].product_qty, 2)
        # Confirm the sale
        self.purchase_order.button_confirm()
        # Ensure we can still update the quantity
        pack_line.product_qty = 4
        self.assertAlmostEqual(self.purchase_order.order_line[1].product_qty, 8)
        self.assertAlmostEqual(self.purchase_order.order_line[2].product_qty, 4)

    def test_do_not_expand(self):
        pack_line = self._add_po_line()
        pack_line_update = pack_line.with_context(update_prices=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)
        pack_line_update = pack_line.with_context(update_pricelist=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)

    def test_create_several_lines(self):
        # Create two sale order lines with two pack products
        self._add_po_line()
        self._add_po_line(sequence=20)
        # Check 6 lines are created
        self.assertEqual(len(self.purchase_order.order_line), 6)
        # Check lines sequences and order are respected
        for po_line in self.purchase_order.order_line[:3]:
            self.assertEqual(po_line.sequence, 10)
        for po_line in self.purchase_order.order_line[3:]:
            self.assertEqual(po_line.sequence, 20)

    def test_order_line_detailed_with_seller(self):
        self.pack.seller_ids = [
            Command.create({"partner_id": self.partner.id, "min_qty": 1, "price": 25})
        ]
        self.component1.seller_ids = [
            Command.create({"partner_id": self.partner.id, "min_qty": 1, "price": 15})
        ]
        self._add_po_line()
        # Check the subtotal corresponding to seller on lines
        self.assertEqual(self.purchase_order.order_line[0].price_subtotal, 25)
        # 15 * 2 qty
        self.assertEqual(self.purchase_order.order_line[1].price_subtotal, 30)
        self.assertEqual(self.purchase_order.order_line[2].price_subtotal, 18)

    def test_order_line_totalized_with_seller(self):
        self.component1.seller_ids = [
            Command.create({"partner_id": self.partner.id, "min_qty": 1, "price": 15})
        ]
        self.pack.pack_component_price = "totalized"
        self._add_po_line()
        # Check the subtotal corresponding to seller on lines
        # component 1: 15 * 2 qty + component2: 18
        self.assertEqual(self.purchase_order.order_line[0].price_subtotal, 48)
        self.assertEqual(self.purchase_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.purchase_order.order_line[2].price_subtotal, 0)
