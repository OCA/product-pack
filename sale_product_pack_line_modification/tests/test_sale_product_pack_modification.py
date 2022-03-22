# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class TestSaleProductPack(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modif_wizard_obj = cls.env["sale.product.pack.line.modification"]
        cls.product_1 = cls.env.ref("product.product_product_1")
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

    def test_change_product(self):
        # Create a sale order line with ignored price configuration (modification restricted)
        # Change one sub line with wizard
        # Check new product is well set
        # Check the line is marked as modified
        # Check if new message is set
        product_cp = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        vals = [
            {
                "order_id": self.sale_order.id,
                "name": product_cp.name,
                "product_id": product_cp.id,
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
