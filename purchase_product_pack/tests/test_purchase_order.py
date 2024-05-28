from odoo.tests.common import TransactionCase


class TestPurchaseOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_12").id,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

        cls.pack_product = cls.env["product.product"].create(
            {
                "name": "Pack Product",
                "type": "consu",
                "pack_ok": True,
                "pack_type": "detailed",
            }
        )

    def test_copy_data(self):
        self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "product_id": self.product.id,
                "name": self.product.name,
                "product_qty": 1,
                "price_unit": 100,
            }
        )

        data = self.purchase_order.copy_data()
        self.assertTrue(data)
        self.assertIn("order_line", data[0])
        self.assertEqual(len(data[0]["order_line"]), 1)
        self.assertEqual(data[0]["order_line"][0][2]["product_id"], self.product.id)
