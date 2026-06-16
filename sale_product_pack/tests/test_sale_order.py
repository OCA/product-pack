# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import UserError

from .common import TestSaleProductPackBase


class TestSaleOrder(TestSaleProductPackBase):
    def test_unlink_pack_line(self):
        """Test the unlink of a pack product line and its components."""
        pack_line = self._add_so_line()
        # Verify 3 lines are created (1 pack + 2 components)
        self.assertEqual(len(self.sale_order.order_line), 3)
        # Unlink the pack line and its components together
        pack_line.pack_child_line_ids.with_context(
            pack_children_force_unlink=True
        ).unlink()
        pack_line.unlink()
        # Verify all pack lines are deleted
        self.assertEqual(len(self.sale_order.order_line), 0)

    def test_unlink_component_line_should_fail(self):
        """Test that unlinking a component line should raise an error."""
        pack_line = self._add_so_line()
        component_line = self.sale_order.order_line.filtered(
            lambda line: line.pack_parent_line_id == pack_line
        )[0]
        # Try to unlink component line directly
        with self.assertRaises(UserError):
            component_line.unlink()
        # Verify line still exists
        self.assertEqual(len(self.sale_order.order_line), 3)

    def test_unlink_component_line_with_forcing_context(self):
        """Test that unlinking a component line should raise an error."""
        pack_line = self._add_so_line()
        component_line = self.sale_order.order_line.filtered(
            lambda line: line.pack_parent_line_id == pack_line
        )[0]
        # Unlink component line directly
        component_line.with_context(pack_children_force_unlink=True).unlink()
        # Verify line has been deleted
        self.assertEqual(len(self.sale_order.order_line), 2)

    def test_unlink_multiple_packs(self):
        """Test unlinking multiple pack lines."""
        pack_line1 = self._add_so_line()
        pack_line2 = self._add_so_line(sequence=20)
        # Verify 6 lines are created (2 packs + 4 components)
        self.assertEqual(len(self.sale_order.order_line), 6)
        # Unlink first pack
        pack_line1.pack_child_line_ids.with_context(
            pack_children_force_unlink=True
        ).unlink()
        pack_line1.unlink()
        # Verify 3 lines remain (1 pack + 2 components of pack2)
        self.assertEqual(len(self.sale_order.order_line), 3)
        # Verify remaining lines belong to pack_line2
        for line in self.sale_order.order_line:
            if line.pack_parent_line_id:
                self.assertEqual(line.pack_parent_line_id, pack_line2)

    def test_unlink_pack_line_with_confirmed_order(self):
        """Test that unlinking a pack line from a confirmed sale order raises error."""
        pack_line = self._add_so_line()
        self.assertEqual(len(self.sale_order.order_line), 3)
        # Confirm the sale order
        self.sale_order.action_confirm()
        # Try to unlink the pack line - should raise error
        with self.assertRaises(UserError):
            pack_line.unlink()

    def test_unlink_non_pack_line_with_pack_lines(self):
        """Test unlinking a non-pack line from an order with pack lines."""
        # Create a non-pack product line
        product = self.env["product.product"].create({"name": "Test product"})
        non_pack_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 1,
                "sequence": 5,
            }
        )
        # Add a pack line
        self._add_so_line()
        # Verify 4 lines are created (1 non-pack + 1 pack + 2 components)
        self.assertEqual(len(self.sale_order.order_line), 4)
        # Unlink the non-pack line
        non_pack_line.unlink()
        # Verify 3 lines remain (1 pack + 2 components)
        self.assertEqual(len(self.sale_order.order_line), 3)
        # Verify pack and component lines still exist
        self.assertEqual(self.sale_order.order_line[0].product_id, self.pack)
        self.assertEqual(self.sale_order.order_line[1].product_id, self.component1)
        self.assertEqual(self.sale_order.order_line[2].product_id, self.component2)

    def test_unlink_pack_line_should_unlink_children(self):
        """Unlinking the parent should remove children too."""
        pack_line = self._add_so_line()
        self.assertEqual(len(self.sale_order.order_line), 3)

        self.sale_order.write({"order_line": [Command.delete(pack_line.id)]})

        self.assertEqual(len(self.sale_order.order_line), 0)
