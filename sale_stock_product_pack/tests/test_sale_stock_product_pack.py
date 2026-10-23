# Copyright 2021 Tecnativa - David Vidal
# Copyright 2025 Tecnativa - Pedro M. Baeza
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.sale_product_pack.tests.common import TestSaleProductPackBase


class TestSaleStockProductPack(TestSaleProductPackBase):
    # Odoo 20 runs each test as _test_user: delivering a pack needs the stock side too
    _test_user_groups = TestSaleProductPackBase._test_user_groups + (
        "stock.group_stock_user",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.pack.type = "consu"
        cls.pack.invoice_policy = "delivery"
        cls.pack.pack_line_ids.product_id.invoice_policy = "delivery"

    def _create_stock_quant(self, product, qty):
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": qty,
            }
        )

    def test_delivered_quantities(self):
        pack_line = self._add_so_line()
        pack_line.product_uom_qty = 9
        self.sale = self.sale_order
        self.sale.action_confirm()
        self.assertEqual(0, pack_line.qty_delivered)
        # Process the picking
        for line in self.sale.picking_ids.move_ids.filtered(
            lambda x: x.product_id != self.pack
        ):
            line.quantity = line.product_uom_qty
        self.sale.picking_ids.move_ids.picked = True
        self.sale.picking_ids._action_done()
        # All components delivered, all the pack quantities should be so
        self.assertEqual(9, pack_line.qty_delivered)

    def _get_aggregated_product_quantities(self, sol):
        sol_data = sol.move_ids.move_line_ids._get_aggregated_product_quantities()
        key_0 = next(iter(sol_data.keys()))
        return sol_data[key_0]

    def test_picking_pack_consu_01(self):
        self.pack.pack_type = "detailed"
        self.component1.is_storable = True
        self.component2.is_storable = True
        sol_pack = self._add_so_line(self.pack)
        self._create_stock_quant(self.component1, 2)
        self._create_stock_quant(self.component2, 1)
        self.sale_order.action_confirm()
        sol_component1 = self.sale_order.order_line.filtered(
            lambda x: x.product_id == self.component1
        )
        sol_component2 = self.sale_order.order_line.filtered(
            lambda x: x.product_id == self.component2
        )
        picking = self.sale_order.picking_ids
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        data_names = []
        aggregated_lines = picking.move_line_ids._get_aggregated_product_quantities()
        for line in aggregated_lines:
            data_names.append(aggregated_lines[line]["name"])
        self.assertEqual(
            data_names, ["Test product pack", "Pack component 1", "Pack component 2"]
        )
        line_product_pack_data = self._get_aggregated_product_quantities(sol_pack)
        self.assertEqual(line_product_pack_data["qty_ordered"], 1)
        self.assertEqual(line_product_pack_data["quantity"], 1)
        line_component1_data = self._get_aggregated_product_quantities(sol_component1)
        self.assertEqual(line_component1_data["qty_ordered"], 2)
        self.assertEqual(line_component1_data["quantity"], 2)
        line_component2_data = self._get_aggregated_product_quantities(sol_component2)
        self.assertEqual(line_component2_data["qty_ordered"], 1)
        self.assertEqual(line_component2_data["quantity"], 1)

    def test_picking_pack_consu_02(self):
        self.pack.pack_type = "detailed"
        self.component1.is_storable = True
        self.component2.is_storable = True
        sol_component1 = self._add_so_line(self.component1, 10)
        sol_component2 = self._add_so_line(self.component2, 11)
        sol_component2.product_uom_qty = 10
        sol_pack = self._add_so_line(self.pack, 12)
        sol_pack.product_uom_qty = 2
        self._create_stock_quant(self.component1, 5)  # 1 + (2*2)
        self._create_stock_quant(self.component2, 12)
        self.sale_order.action_confirm()
        sol_pack_component1 = self.sale_order.order_line.filtered(
            lambda x: (
                x.pack_parent_line_id == sol_pack and x.product_id == self.component1
            )
        )
        sol_pack_component2 = self.sale_order.order_line.filtered(
            lambda x: (
                x.pack_parent_line_id == sol_pack and x.product_id == self.component2
            )
        )
        picking = self.sale_order.picking_ids
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        data_names = []
        aggregated_lines = picking.move_line_ids._get_aggregated_product_quantities()
        for line in aggregated_lines:
            data_names.append(aggregated_lines[line]["name"])
        self.assertEqual(
            data_names,
            [
                "Pack component 1",
                "Pack component 2",
                "Test product pack",
                "Pack component 1",
                "Pack component 2",
            ],
        )
        line_component1_data = self._get_aggregated_product_quantities(sol_component1)
        self.assertEqual(line_component1_data["qty_ordered"], 1)
        self.assertEqual(line_component1_data["quantity"], 1)
        line_component2_data = self._get_aggregated_product_quantities(sol_component2)
        self.assertEqual(line_component2_data["qty_ordered"], 10)
        self.assertEqual(line_component2_data["quantity"], 10)
        line_pack_data = self._get_aggregated_product_quantities(sol_pack)
        self.assertEqual(line_pack_data["qty_ordered"], 2)
        self.assertEqual(line_pack_data["quantity"], 2)
        line_pack_component1_data = self._get_aggregated_product_quantities(
            sol_pack_component1
        )
        self.assertEqual(line_pack_component1_data["qty_ordered"], 4)
        self.assertEqual(line_pack_component1_data["quantity"], 4)
        line_pack_component2_data = self._get_aggregated_product_quantities(
            sol_pack_component2
        )
        self.assertEqual(line_pack_component2_data["qty_ordered"], 2)
        self.assertEqual(line_pack_component2_data["quantity"], 2)
