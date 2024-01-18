# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import Form, SavepointCase


class TestSaleProductPack(SavepointCase):
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
        pack_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == product_cp
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

    def test_update_qty_do_not_expand(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        main_sol = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        main_sol.with_context(update_prices=True).product_uom_qty = 2
        self.assertTrue(
            all(
                self.sale_order.order_line.filtered(
                    lambda sol: sol.pack_parent_line_id == main_sol
                ).mapped(lambda sol: sol.product_uom_qty == 1)
            ),
        )

    def test_update_pack_qty_with_new_component(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        main_sol = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )

        self.assertEqual(
            sum(
                self.sale_order.order_line.filtered(
                    lambda sol: sol.pack_parent_line_id == main_sol
                ).mapped("product_uom_qty")
            ),
            3,
            "Expected 3 lines with quantity 1 while setup this test",
        )

        product_cp.pack_line_ids |= self.env["product.pack.line"].create(
            {
                "parent_product_id": product_cp.id,
                "product_id": self.env.ref("product.product_product_12").id,
                "quantity": 2,
            }
        )

        main_sol.product_uom_qty = 2
        self.assertEqual(
            sum(
                self.sale_order.order_line.filtered(
                    lambda sol: sol.pack_parent_line_id == main_sol
                ).mapped("product_uom_qty")
            ),
            10,
            "Expected 3 lines with quantity 2 and new component line with quantity 4",
        )

    def test_update_pack_qty_with_new_component_do_not_expand(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        main_sol = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )

        self.assertEqual(
            sum(
                self.sale_order.order_line.filtered(
                    lambda sol: sol.pack_parent_line_id == main_sol
                ).mapped("product_uom_qty")
            ),
            3,
            "Expected 3 lines with quantity 1 while setup this test",
        )

        product_cp.pack_line_ids |= self.env["product.pack.line"].create(
            {
                "parent_product_id": product_cp.id,
                "product_id": self.env.ref("product.product_product_12").id,
                "quantity": 2,
            }
        )

        main_sol.with_context(update_prices=True).product_uom_qty = 2
        self.assertEqual(
            sum(
                self.sale_order.order_line.filtered(
                    lambda sol: sol.pack_parent_line_id == main_sol
                ).mapped("product_uom_qty")
            ),
            3,
            "Expected 3 lines with quantity 2 and no new component line",
        )

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

    def test_create_several_lines(self):
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

    def test_copy_sale_order_with_detailed_product_pack(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        copied_order = self.sale_order.copy()
        copied_order_component_lines_pack_line = copied_order.order_line.filtered(
            lambda line: line.product_id.pack_ok
        )
        copied_order_component_lines = copied_order.order_line.filtered(
            lambda line: line.pack_parent_line_id
        )
        self.assertEqual(
            copied_order_component_lines.pack_parent_line_id,
            copied_order_component_lines_pack_line,
        )

    def test_check_pack_line_unlink(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        with Form(self.sale_order) as so_form:
            with self.assertRaisesRegex(
                UserError,
                "You cannot delete this line because is part of a pack in this "
                "sale order. In order to delete this line you need to delete the "
                "pack itself",
            ):
                so_form.order_line.remove(len(self.sale_order.order_line) - 1)

    def test_unlink_pack_form_proxy(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        with Form(self.sale_order) as so_form:
            so_form.order_line.remove(0)
            so_form.save()
        self.assertEqual(len(self.sale_order.order_line), 0)

    def test_unlink_pack_record_unlink(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        pack_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id.pack_ok
        )
        pack_line.unlink()
        self.assertEqual(len(self.sale_order.order_line), 0)

    def test_unlink_pack_old_style_like_ui(self):
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
                "product_uom_qty": 1,
            }
        )
        pack_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id.pack_ok
        )
        self.sale_order.write({"order_line": [(2, pack_line.id)]})
        self.assertEqual(len(self.sale_order.order_line), 0)
