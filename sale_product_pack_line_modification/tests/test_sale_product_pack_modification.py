# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import SaleProductPackLineModificationCommon


class TestSaleProductPack(SaleProductPackLineModificationCommon):
    def test_change_product(self):
        # Create a sale order line with ignored price configuration
        # (modification restricted)
        # Change one sub line with wizard
        # Check new product is well set
        # Check the line is marked as modified
        # Check if new message is set
        vals = [
            {
                "order_id": self.sale_order.id,
                "name": self.product_cp.name,
                "product_id": self.product_cp.id,
                "product_uom_qty": 1,
            },
        ]
        self.env["sale.order.line"].create(vals)
        self.assertEqual(len(self.sale_order.order_line), 4)

        line_to_change = self.sale_order.order_line[1]
        messages_before = self.sale_order.message_ids

        wizard = self.modif_wizard_obj.with_context(
            active_ids=self.sale_order.order_line[1].ids, active_model="sale.order.line"
        ).create({"product_id": self.product_1.id, "product_quantity": 3.0})
        self.assertEqual(wizard.sale_order_line_ids, line_to_change)
        wizard.doit()
        self.assertEqual(line_to_change.product_id, self.product_1)
        self.assertEqual(line_to_change.product_uom_qty, 3.0)
        self.assertTrue(line_to_change.pack_modified_line)
        messages_after = self.sale_order.message_ids - messages_before
        self.assertEqual(1, len(messages_after))
