# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestPurchaseOrderCopyAndDelete(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.partner.id})
        cls.pack = cls.env.ref("product_pack.product_pack_cpu_detailed_components")

    def _create_pack_parent_line(self):
        """Create a parent pack line on the purchase order."""
        return self.env["purchase.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.pack.id,
                "name": self.pack.name,
                "product_qty": 1.0,
            }
        )

    def test_copy_data_skips_pack_child_lines(self):
        """copy_data should not duplicate pack child lines."""
        parent = self._create_pack_parent_line()
        # parent + children must exist
        self.assertGreater(len(self.order.order_line), 1)

        data = self.order.copy_data()[0]
        line_cmds = data["order_line"]

        # Only the parent pack line should be copied
        self.assertEqual(len(line_cmds), 1)
        self.assertEqual(line_cmds[0][2]["product_id"], parent.product_id.id)

    def test_check_deleted_line_marks_subpacks(self):
        """_check_deleted_line must mark child pack lines for deletion."""
        parent = self._create_pack_parent_line()
        children = self.order.order_line - parent
        self.assertTrue(children)

        child = children[0]
        vals = {
            "order_line": [
                # delete parent
                [2, parent.id, False],
                # child is passed without delete flag
                [1, child.id, {"product_qty": child.product_qty}],
            ]
        }

        self.order._check_deleted_line(vals)

        # The child line must be converted to a delete command (code 2)
        self.assertEqual(vals["order_line"][1][0], 2)


@tagged("-at_install", "post_install")
class TestPurchaseOrderLineActions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.order = cls.env["purchase.order"].create({"partner_id": cls.partner.id})
        cls.pack = cls.env.ref("product_pack.product_pack_cpu_detailed_components")

    def test_action_open_parent_pack_product_view(self):
        """Action must open a product.product view filtered on the parent pack."""
        parent = self.env["purchase.order.line"].create(
            {
                "order_id": self.order.id,
                "product_id": self.pack.id,
                "name": self.pack.name,
                "product_qty": 1.0,
            }
        )
        child = (self.order.order_line - parent)[0]

        action = child.action_open_parent_pack_product_view()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "product.product")
        self.assertIn("domain", action)
        self.assertTrue(action["domain"])
