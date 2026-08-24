# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo import Command

from .common import TestSaleProductPackBase


class TestSaleProductPack(TestSaleProductPackBase):
    def test_create_components_price_order_line(self):
        group_discount = self.env.ref("sale.group_discount_per_so_line")
        self.env.user.write({"group_ids": [(4, group_discount.id)]})
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

    def test_non_detailed_modifiable_pack(self):
        """Test non_detailed pack with pack_modifiable auto-expands."""
        # Configure pack as non_detailed with pack_modifiable
        self.pack.pack_type = "non_detailed"
        self.pack.pack_modifiable = True
        self._add_so_line()
        # After create, pack should be transformed into:
        # 1 section line + 1 pack line + 2 component lines
        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        self.assertEqual(len(ordered_lines), 4)
        section_line = ordered_lines[0]
        self.assertEqual(section_line.display_type, "line_section")
        self.assertEqual(section_line.name, self.pack.display_name)
        self.assertTrue(section_line.collapse_composition)
        pack_line = ordered_lines[1]
        self.assertEqual(pack_line.product_id, self.pack)
        self.assertFalse(pack_line.display_type)
        # Pack line shows its own base price (list_price=10), not the totalized sum.
        self.assertAlmostEqual(pack_line.price_subtotal, 10)
        # Next lines should be the components
        self.assertEqual(ordered_lines[2].product_id, self.component1)
        self.assertEqual(ordered_lines[3].product_id, self.component2)
        # Component lines have their real unit prices; pack line keeps its base price.
        self.assertEqual(ordered_lines[2].product_uom_qty, 2)
        self.assertEqual(ordered_lines[3].product_uom_qty, 1)
        self.assertAlmostEqual(ordered_lines[2].price_unit, 20)
        self.assertAlmostEqual(ordered_lines[3].price_unit, 30)
        self.assertAlmostEqual(ordered_lines[2].price_subtotal, 40)
        self.assertAlmostEqual(ordered_lines[3].price_subtotal, 30)
        # Total = base pack (10) + components (40 + 30) — no double billing.
        self.assertAlmostEqual(self.sale_order.amount_untaxed, 80)
        # Lines should be editable (no pack_parent_line_id)
        self.assertFalse(pack_line.pack_parent_line_id)
        self.assertFalse(ordered_lines[2].pack_parent_line_id)
        self.assertFalse(ordered_lines[3].pack_parent_line_id)

        # Updating the pack quantity should update component quantities.
        pack_line.product_uom_qty = 2
        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        self.assertEqual(ordered_lines[2].product_uom_qty, 4)
        self.assertEqual(ordered_lines[3].product_uom_qty, 2)

    def test_non_detailed_modifiable_pack_discount(self):
        """The pack line sale_discount must reach the expanded component lines."""
        group_discount = self.env.ref("sale.group_discount_per_so_line")
        self.env.user.write({"group_ids": [(4, group_discount.id)]})
        self.pack.pack_type = "non_detailed"
        self.pack.pack_modifiable = True
        self.pack_line1.sale_discount = 10.0
        self.pack_line2.sale_discount = 10.0
        self._add_so_line()
        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        pack_line = ordered_lines[1]
        # The pack product line keeps its own base price with no discount.
        self.assertEqual(pack_line.product_id, self.pack)
        self.assertAlmostEqual(pack_line.discount, 0)
        self.assertAlmostEqual(pack_line.price_subtotal, 10)
        # Component lines carry the sale_discount of their product.pack.line.
        self.assertEqual(ordered_lines[2].product_id, self.component1)
        self.assertEqual(ordered_lines[3].product_id, self.component2)
        self.assertAlmostEqual(ordered_lines[2].discount, 10)
        self.assertAlmostEqual(ordered_lines[3].discount, 10)
        # 20 * 2 * 0.9 = 36 ; 30 * 1 * 0.9 = 27
        self.assertAlmostEqual(ordered_lines[2].price_subtotal, 36)
        self.assertAlmostEqual(ordered_lines[3].price_subtotal, 27)
        # Total = base pack (10) + discounted components (36 + 27).
        self.assertAlmostEqual(self.sale_order.amount_untaxed, 73)
        # The discount survives a quantity change on the pack line.
        pack_line.product_uom_qty = 2
        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        self.assertAlmostEqual(ordered_lines[2].discount, 10)
        self.assertAlmostEqual(ordered_lines[3].discount, 10)

    def test_non_detailed_modifiable_pack_copy(self):
        """Duplicating an order with a non-detailed modifiable pack."""
        self.pack.pack_type = "non_detailed"
        self.pack.pack_modifiable = True
        self._add_so_line()

        copied_order = self.sale_order.copy()

        ordered_lines = copied_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        # Expect exactly 1 section + 1 pack + 2 components — same as original.
        self.assertEqual(len(ordered_lines), 4)
        self.assertEqual(ordered_lines[0].display_type, "line_section")
        self.assertTrue(ordered_lines[0].collapse_composition)
        pack_line = ordered_lines[1]
        self.assertEqual(pack_line.product_id, self.pack)
        self.assertAlmostEqual(pack_line.price_subtotal, 10)
        self.assertEqual(ordered_lines[2].product_id, self.component1)
        self.assertAlmostEqual(ordered_lines[2].price_unit, 20)
        self.assertEqual(ordered_lines[3].product_id, self.component2)
        self.assertAlmostEqual(ordered_lines[3].price_unit, 30)
        # Total must not be inflated by double-copying components.
        self.assertAlmostEqual(copied_order.amount_untaxed, 80)

    def test_non_detailed_modifiable_pack_with_nested_pack_not_expanded(self):
        nested_pack = self.env["product.product"].create(
            {
                "name": "Nested pack",
                "company_id": self.env.company.id,
                "type": "service",
                "list_price": 5,
                "pack_ok": True,
                "pack_type": "non_detailed",
                "pack_component_price": "detailed",
                "pack_line_ids": [
                    Command.create({"product_id": self.component1.id, "quantity": 1}),
                ],
            }
        )
        self.pack.pack_type = "non_detailed"
        self.pack.pack_modifiable = True
        self.pack.pack_line_ids = [
            Command.clear(),
            Command.create({"product_id": nested_pack.id, "quantity": 1}),
            Command.create({"product_id": self.component2.id, "quantity": 1}),
        ]

        self._add_so_line()

        # Pack should expand: section + pack line + nested pack + component2.
        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        self.assertEqual(len(ordered_lines), 4)

        # First line should be a standard Odoo section.
        section_line = ordered_lines[0]
        self.assertEqual(section_line.display_type, "line_section")

        # Second line should be the pack product.
        pack_line = ordered_lines[1]
        self.assertEqual(pack_line.product_id, self.pack)

        # Third line should be the nested pack (not expanded)
        nested_line = ordered_lines[2]
        self.assertEqual(nested_line.product_id, nested_pack)

        # Fourth line should be the regular component
        component_line = ordered_lines[3]
        self.assertEqual(component_line.product_id, self.component2)

    def test_non_detailed_modifiable_pack_catalog_add_accumulates_without_section_dup(
        self,
    ):
        self.pack.pack_type = "non_detailed"
        self.pack.pack_modifiable = True

        class DummyRequest:
            @staticmethod
            def update_context(**kwargs):
                return kwargs

        with patch("odoo.addons.sale.models.sale_order.request", DummyRequest()):
            self.sale_order._update_order_line_info(self.pack.id, 1)
            self.sale_order._update_order_line_info(self.pack.id, 2)

        ordered_lines = self.sale_order.order_line.sorted(
            key=lambda line: (line.sequence, line.id)
        )
        sections = ordered_lines.filtered(
            lambda line: line.display_type == "line_section"
        )
        pack_lines = ordered_lines.filtered(
            lambda line: not line.display_type and line.product_id == self.pack
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(len(pack_lines), 1)
        self.assertEqual(pack_lines.product_uom_qty, 2)

        self.assertEqual(ordered_lines[2].product_id, self.component1)
        self.assertEqual(ordered_lines[3].product_id, self.component2)
        self.assertEqual(ordered_lines[2].product_uom_qty, 4)
        self.assertEqual(ordered_lines[3].product_uom_qty, 2)
