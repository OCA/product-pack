# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import TestSaleProductPackBase


class TestSaleProductPack(TestSaleProductPackBase):
    def test_create_components_price_order_line(self):
        group_discount = self.env.ref("sale.group_discount_per_so_line")
        self.env.user.write({"groups_id": [(4, group_discount.id)]})
        self._add_so_line()
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 3)
        # Check if sequence is the same as pack product one
        for so_line in self.sale_order.order_line:
            self.assertEqual(so_line.sequence, 10)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(self.sale_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.sale_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.sale_order.order_line[2].product_id, self.component2)
        # Price before update pricelist
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 10)
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 40)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 30)
        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertEqual(self.sale_order.order_line[0].discount, 10)
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 9)
        self.assertEqual(self.sale_order.order_line[1].discount, 10)
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 36)
        self.assertEqual(self.sale_order.order_line[2].discount, 10)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 27)

    def test_create_ignored_price_order_line(self):
        self.pack.pack_component_price = "ignored"
        self._add_so_line()
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 3)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(self.sale_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.sale_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.sale_order.order_line[2].product_id, self.component2)
        # All component lines have zero as subtotal
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 0)
        # Pack price is different from the sum of component prices
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 10)
        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 9)
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 0)

    def test_create_totalized_price_order_line(self):
        self.pack.pack_component_price = "totalized"
        self._add_so_line()
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 3)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(self.sale_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.sale_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.sale_order.order_line[2].product_id, self.component2)
        # All component lines have zero as subtotal
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 0)
        # Pack price is equal to the sum of component prices
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 70)
        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertEqual(self.sale_order.order_line[0].price_subtotal, 63)
        self.assertEqual(self.sale_order.order_line[1].price_subtotal, 0)
        self.assertEqual(self.sale_order.order_line[2].price_subtotal, 0)

    def test_create_non_detailed_price_order_line(self):
        self.pack.pack_type = "non_detailed"
        self._add_so_line()
        # After create, there will be only one line, because product_type is
        # not a detailed one
        self.assertEqual(len(self.sale_order.order_line), 1)
        # Pack price is equal to the sum of component prices
        self.assertEqual(self.sale_order.order_line.price_subtotal, 70)
        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertEqual(self.sale_order.order_line.price_subtotal, 63)

    def test_update_qty(self):
        pack_line = self._add_so_line()
        # change qty of main sol and ensure all the quantities have doubled
        pack_line.product_uom_qty = 2
        self.assertAlmostEqual(self.sale_order.order_line[1].product_uom_qty, 4)
        self.assertAlmostEqual(self.sale_order.order_line[2].product_uom_qty, 2)
        # Confirm the sale
        self.sale_order.action_confirm()
        # Ensure we can still update the quantity
        pack_line.product_uom_qty = 4
        self.assertAlmostEqual(self.sale_order.order_line[1].product_uom_qty, 8)
        self.assertAlmostEqual(self.sale_order.order_line[2].product_uom_qty, 4)

    def test_do_not_expand(self):
        pack_line = self._add_so_line()
        pack_line_update = pack_line.with_context(update_prices=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)
        pack_line_update = pack_line.with_context(update_pricelist=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)

    def test_create_several_lines_01(self):
        # Create two sale order lines with two pack products
        self._add_so_line()
        self._add_so_line(sequence=20)
        # Check 6 lines are created
        self.assertEqual(len(self.sale_order.order_line), 6)
        # Check lines sequences and order are respected
        for so_line in self.sale_order.order_line[:3]:
            self.assertEqual(so_line.sequence, 10)
        for so_line in self.sale_order.order_line[3:]:
            self.assertEqual(so_line.sequence, 20)

    def test_create_several_lines_02(self):
        # Create several sale order lines
        product = self.env["product.product"].create({"name": "Test product"})
        self._add_so_line(product=product)
        self._add_so_line(sequence=20)
        self._add_so_line(product=product, sequence=30)
        # After create, there will be 4 lines (1 + 3 + 1)
        self.assertEqual(len(self.sale_order.order_line), 5)
        # Check if lines are well ordered
        self.assertEqual(self.sale_order.order_line[0].product_id, product)
        self.assertEqual(self.sale_order.order_line[1].product_id, self.pack)
        self.assertEqual(self.sale_order.order_line[2].product_id, self.component1)
        self.assertEqual(self.sale_order.order_line[3].product_id, self.component2)
        self.assertEqual(self.sale_order.order_line[4].product_id, product)
