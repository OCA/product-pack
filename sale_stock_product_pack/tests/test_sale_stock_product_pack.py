# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, TransactionCase


class TestSaleStockProductPack(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_pack = cls.env.ref(
            "product_pack.product_pack_cpu_detailed_components"
        )
        cls.product_pack.type = "product"
        cls.product_pack.invoice_policy = "delivery"
        cls.product_pack.pack_line_ids.product_id.invoice_policy = "delivery"
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        with sale_form.order_line.new() as line:
            line.product_id = cls.product_pack
            line.product_uom_qty = 9
        cls.sale = sale_form.save()
        cls.sale.action_confirm()

    def test_delivered_quantities(self):
        pack_line = self.sale.order_line.filtered(
            lambda x: x.product_id == self.product_pack
        )
        self.assertEqual(0, pack_line.qty_delivered)
        # Process the picking
        for line in self.sale.picking_ids.move_ids.filtered(
            lambda x: x.product_id != self.product_pack
        ):
            line.quantity = line.product_uom_qty
        self.sale.picking_ids.move_ids.picked = True
        self.sale.picking_ids._action_done()
        # All components delivered, all the pack quantities should be so
        # TODO: it needs to compute twice. In view it does it fine.
        self.sale.order_line.mapped("qty_delivered")
        self.assertEqual(9, pack_line.qty_delivered)
