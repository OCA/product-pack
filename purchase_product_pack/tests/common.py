# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.product_pack.tests.common import ProductPackCommon


class TestPurchaseProductPackBase(ProductPackCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test purchase pack"})
        cls.pack.standard_price = 5
        cls.component1.standard_price = 12
        cls.component2.standard_price = 18
        cls.purchase_order = cls.env["purchase.order"].create(
            {"partner_id": cls.partner.id}
        )

    def _add_po_line(self, product=None, sequence=10):
        product = product or self.pack
        return self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "name": product.name,
                "product_id": product.id,
                "product_qty": 1,
                "sequence": sequence,
            }
        )
