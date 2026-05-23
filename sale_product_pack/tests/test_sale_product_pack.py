# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class TestSaleProductPack(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test",
                "company_id": cls.env.company.id,
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
        cls.discount_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Discount",
                "company_id": cls.env.company.id,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "percentage",
                            "percent_price": 10,
                        },
                    )
                ],
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "pricelist_id": pricelist.id,
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

    def test_create_components_price_order_line(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 4)
        pack_line = self.sale_order.order_line.filtered(
            lambda pline: pline.product_id == product_cp
        )
        # Check if sequence is the same as pack product one
        sequence = pack_line.sequence
        self.assertEqual(
            [sequence, sequence, sequence, sequence],
            self.sale_order.order_line.mapped("sequence"),
        )
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            self.sale_order.order_line.mapped("product_id"),
            product_cp | product_cp.get_pack_lines().mapped("product_id"),
        )
        # Price before update pricelist
        self.assertAlmostEqual(line.price_subtotal, 30.75)
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"),
            [1755.0, 22.5, 885.0],
        )
        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertAlmostEqual(line.price_subtotal, 27.68)
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"),
            [1579.5, 20.25, 796.5],
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
        self.assertAlmostEqual(line.price_subtotal, 30.75)
        self.assertNotEqual(self._get_component_prices_sum(product_tp), 30.75)

        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertAlmostEqual(line.price_subtotal, 27.68)
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )

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
        self.assertAlmostEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )
        # Pack price is equal to the sum of component prices
        self.assertAlmostEqual(line.price_subtotal, 2662.5)
        self.assertAlmostEqual(self._get_component_prices_sum(product_tp), 2662.5)

        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertAlmostEqual(line.price_subtotal, 2396.25)
        self.assertEqual(
            (self.sale_order.order_line - line).mapped("price_subtotal"), [0, 0, 0]
        )

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
        self.assertAlmostEqual(line.price_subtotal, 2662.5)
        self.assertAlmostEqual(self._get_component_prices_sum(product_ndtp), 2662.5)

        # Update pricelist with a discount
        self.sale_order.pricelist_id = self.discount_pricelist
        self.sale_order.action_update_prices()
        self.assertAlmostEqual(line.price_subtotal, 2396.25)

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
        self.assertAlmostEqual(total_qty_init * 2, total_qty_updated)

        # Confirm the sale
        self.sale_order.action_confirm()

        # Ensure we can still update the quantity
        main_sol.product_uom_qty = 2 * main_sol.product_uom_qty
        total_qty_confirmed = qty_in_order()
        self.assertAlmostEqual(total_qty_updated * 2, total_qty_confirmed)

    def test_do_not_expand(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        pack_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        # After create, there will be four lines
        self.assertEqual(len(self.sale_order.order_line), 4)
        pack_line_update = pack_line.with_context(update_prices=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)
        pack_line_update = pack_line.with_context(update_pricelist=True)
        self.assertTrue(pack_line_update.do_no_expand_pack_lines)

    def test_create_several_lines_01(self):
        # Create two sale order lines with two pack products
        # Check 8 lines are created
        # Check lines sequences and order are respected
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        product_tp = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        vals = [
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            },
            {
                "order_id": self.sale_order.id,
                "name": product_tp.name,
                "product_id": product_tp.id,
                "product_uom_qty": 1,
            },
        ]
        self.env["sale.order.line"].create(vals)
        # After create, there will be eight lines (4 + 4)
        self.assertEqual(len(self.sale_order.order_line), 8)
        # Check if lines are well ordered
        self.assertEqual(self.sale_order.order_line[0].product_id, product_cp)
        sequence_cp = self.sale_order.order_line[0].sequence
        self.assertEqual(sequence_cp, self.sale_order.order_line[1].sequence)
        self.assertEqual(sequence_cp, self.sale_order.order_line[2].sequence)
        self.assertEqual(sequence_cp, self.sale_order.order_line[3].sequence)

        self.assertEqual(self.sale_order.order_line[4].product_id, product_tp)
        sequence_tp = self.sale_order.order_line[4].sequence
        self.assertEqual(sequence_tp, self.sale_order.order_line[5].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[6].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[7].sequence)

    def test_create_several_lines_02(self):
        # Create two sale order lines with pack product
        # Check 5 lines are created
        # Check lines sequences and order are respected
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        product = self.env["product.product"].create({"name": "Test product"})
        vals = [
            {
                "order_id": self.sale_order.id,
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 1,
            },
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            },
        ]
        self.env["sale.order.line"].create(vals)
        # After create, there will be eight lines (1 + 4)
        self.assertEqual(len(self.sale_order.order_line), 5)
        # Check if lines are well ordered
        self.assertEqual(self.sale_order.order_line[0].product_id, product)
        self.assertEqual(self.sale_order.order_line[1].product_id, product_cp)
        sequence_tp = self.sale_order.order_line[1].sequence
        self.assertEqual(sequence_tp, self.sale_order.order_line[2].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[3].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[4].sequence)

    def test_create_several_lines_03(self):
        # Create two sale order lines with pack product
        # Check 5 lines are created
        # Check lines sequences and order are respected
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        product = self.env["product.product"].create({"name": "Test product"})
        vals = [
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            },
            {
                "order_id": self.sale_order.id,
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 1,
            },
        ]
        self.env["sale.order.line"].create(vals)
        # After create, there will be eight lines (4 + 1)
        self.assertEqual(len(self.sale_order.order_line), 5)
        # Check if lines are well ordered
        self.assertEqual(self.sale_order.order_line[0].product_id, product_cp)
        sequence_tp = self.sale_order.order_line[0].sequence
        self.assertEqual(sequence_tp, self.sale_order.order_line[1].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[2].sequence)
        self.assertEqual(sequence_tp, self.sale_order.order_line[3].sequence)
        self.assertEqual(self.sale_order.order_line[4].product_id, product)
