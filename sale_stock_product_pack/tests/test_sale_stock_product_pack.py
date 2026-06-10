# Copyright 2021 Tecnativa - David Vidal
# Copyright 2024-2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSaleStockProductPack(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_all = cls.env.ref("product.product_category_all")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.component_1 = cls.env["product.product"].create(
            {
                "name": "Component 1",
                "detailed_type": "product",
                "categ_id": cls.category_all.id,
            }
        )
        cls.component_2 = cls.env["product.product"].create(
            {
                "name": "Component 2",
                "detailed_type": "product",
                "categ_id": cls.category_all.id,
            }
        )
        cls.product_pack = cls.env["product.product"].create(
            {
                "name": "Pack (consumable)",
                "detailed_type": "consu",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": cls.category_all.id,
                "pack_line_ids": [
                    Command.create(
                        {"product_id": cls.component_1.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_2.id, "quantity": 1},
                    ),
                ],
            }
        )

    def _create_sale_order(self, lines):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        for line_data in lines:
            with sale_form.order_line.new() as line:
                line.product_id = line_data[0]
                line.product_uom_qty = line_data[1]
        return sale_form.save()

    def _create_stock_quant(self, product, qty):
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": qty,
            }
        )

    def test_delivered_quantities(self):
        self.product_pack.type = "product"
        self.product_pack.invoice_policy = "delivery"
        self.product_pack.pack_line_ids.product_id.invoice_policy = "delivery"
        sale = self._create_sale_order([(self.product_pack, 9)])
        sale.action_confirm()
        pack_line = sale.order_line.filtered(
            lambda x: x.product_id == self.product_pack
        )
        self.assertEqual(0, pack_line.qty_delivered)
        # Process the picking
        for line in sale.picking_ids.move_ids.filtered(
            lambda x: x.product_id != self.product_pack
        ):
            line.quantity_done = line.product_uom_qty
        sale.picking_ids._action_done()
        # All components delivered, all the pack quantities should be so
        # TODO: it needs to compute twice. In view it does it fine.
        sale.order_line.mapped("qty_delivered")
        self.assertEqual(9, pack_line.qty_delivered)

    def _get_aggregated_product_quantities(self, sol):
        sol_data = sol.move_ids.move_line_ids._get_aggregated_product_quantities()
        key_0 = list(sol_data.keys())[0]
        return sol_data[key_0]

    def test_picking_pack_consu_01(self):
        sale = self._create_sale_order([(self.product_pack, 1)])
        sol_product_pack = sale.order_line.filtered(
            lambda x: x.product_id == self.product_pack
        )
        sol_component_1 = sale.order_line.filtered(
            lambda x: x.product_id == self.component_1
        )
        sol_component_2 = sale.order_line.filtered(
            lambda x: x.product_id == self.component_2
        )
        self._create_stock_quant(self.component_1, 1)
        self._create_stock_quant(self.component_2, 1)
        sale.action_confirm()
        picking = sale.picking_ids
        res = picking.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        wizard.process()
        self.assertEqual(picking.state, "done")
        data_names = []
        aggregated_lines = picking.move_line_ids._get_aggregated_product_quantities()
        for line in aggregated_lines:
            data_names.append(aggregated_lines[line]["name"])
        self.assertEqual(
            data_names, ["Pack (consumable)", "Component 1", "Component 2"]
        )
        line_product_pack_data = self._get_aggregated_product_quantities(
            sol_product_pack
        )
        self.assertEqual(line_product_pack_data["qty_ordered"], 1)
        self.assertEqual(line_product_pack_data["qty_done"], 1)
        line_component_1_data = self._get_aggregated_product_quantities(sol_component_1)
        self.assertEqual(line_component_1_data["qty_ordered"], 1)
        self.assertEqual(line_component_1_data["qty_done"], 1)
        line_component_2_data = self._get_aggregated_product_quantities(sol_component_2)
        self.assertEqual(line_component_2_data["qty_ordered"], 1)
        self.assertEqual(line_component_2_data["qty_done"], 1)

    def test_picking_pack_consu_02(self):
        sale = self._create_sale_order(
            [(self.component_1, 1), (self.component_2, 10), (self.product_pack, 2)]
        )
        sol_component_1 = sale.order_line.filtered(
            lambda x: x.product_id == self.component_1 and not x.pack_parent_line_id
        )
        sol_component_2 = sale.order_line.filtered(
            lambda x: x.product_id == self.component_2 and not x.pack_parent_line_id
        )
        sol_product_pack = sale.order_line.filtered(
            lambda x: x.product_id == self.product_pack
        )
        sol_product_pack_component_1 = sale.order_line.filtered(
            lambda x: x.pack_parent_line_id == sol_product_pack
            and x.product_id == self.component_1
        )
        sol_product_pack_component_2 = sale.order_line.filtered(
            lambda x: x.pack_parent_line_id == sol_product_pack
            and x.product_id == self.component_2
        )
        self._create_stock_quant(self.component_1, 3)
        self._create_stock_quant(self.component_2, 12)
        sale.action_confirm()
        picking = sale.picking_ids
        res = picking.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        wizard.process()
        self.assertEqual(picking.state, "done")
        data_names = []
        aggregated_lines = picking.move_line_ids._get_aggregated_product_quantities()
        for line in aggregated_lines:
            data_names.append(aggregated_lines[line]["name"])
        self.assertEqual(
            data_names,
            [
                "Component 1",
                "Component 2",
                "Pack (consumable)",
                "Component 1",
                "Component 2",
            ],
        )
        line_component_1_data = self._get_aggregated_product_quantities(sol_component_1)
        self.assertEqual(line_component_1_data["qty_ordered"], 1)
        self.assertEqual(line_component_1_data["qty_done"], 1)
        line_component_2_data = self._get_aggregated_product_quantities(sol_component_2)
        self.assertEqual(line_component_2_data["qty_ordered"], 10)
        self.assertEqual(line_component_2_data["qty_done"], 10)
        line_product_pack_data = self._get_aggregated_product_quantities(
            sol_product_pack
        )
        self.assertEqual(line_product_pack_data["qty_ordered"], 2)
        self.assertEqual(line_product_pack_data["qty_done"], 2)
        line_product_pack_component_1_data = self._get_aggregated_product_quantities(
            sol_product_pack_component_1
        )
        self.assertEqual(line_product_pack_component_1_data["qty_ordered"], 2)
        self.assertEqual(line_product_pack_component_1_data["qty_done"], 2)
        line_product_pack_component_2_data = self._get_aggregated_product_quantities(
            sol_product_pack_component_2
        )
        self.assertEqual(line_product_pack_component_2_data["qty_ordered"], 2)
        self.assertEqual(line_product_pack_component_2_data["qty_done"], 2)
