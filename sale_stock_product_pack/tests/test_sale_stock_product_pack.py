# Copyright 2021 Tecnativa - David Vidal
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
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
                    (
                        0,
                        0,
                        {"product_id": cls.component_1.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.component_2.id, "quantity": 1},
                    ),
                ],
            }
        )

    def _create_sale_order(self, product, qty):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        with sale_form.order_line.new() as line:
            line.product_id = product
            line.product_uom_qty = qty
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
        sale = self._create_sale_order(self.product_pack, 9)
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

    def test_picking_pack_consu(self):
        sale = self._create_sale_order(self.product_pack, 1)
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

    def test_picking_validate_partial_pack(self):
        sale = self._create_sale_order(self.product_pack, 2)
        self._create_stock_quant(self.component_1, 2)
        self._create_stock_quant(self.component_2, 2)
        sale.action_confirm()
        picking = sale.picking_ids
        picking_pack = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_pack
        )
        component_moves = picking.move_ids.filtered(
            lambda m: m.product_id != self.product_pack
        )
        for component_move in component_moves:
            self.assertEqual(component_move.quantity_done, 0)
        picking_pack.quantity_done = 1
        picking_pack._onchange_quantity_done()
        for component_move in component_moves:
            self.assertEqual(component_move.quantity_done, 1)
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(picking.state, "done")
        for order_line in sale.order_line:
            self.assertEqual(order_line.product_uom_qty, 2)
            self.assertEqual(order_line.qty_delivered, 1)

    def test_picking_validate_and_partial_return(self):
        sale = self._create_sale_order(self.product_pack, 2)
        self._create_stock_quant(self.component_1, 2)
        self._create_stock_quant(self.component_2, 2)
        sale.action_confirm()
        picking = sale.picking_ids
        picking_pack = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_pack
        )
        component_moves = picking.move_ids.filtered(
            lambda m: m.product_id != self.product_pack
        )
        for component_move in component_moves:
            self.assertEqual(component_move.quantity_done, 0)
        picking_pack.quantity_done = 2
        picking_pack._onchange_quantity_done()
        for component_move in component_moves:
            self.assertEqual(component_move.quantity_done, 2)
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        for order_line in sale.order_line:
            self.assertEqual(order_line.product_uom_qty, 2)
            self.assertEqual(order_line.qty_delivered, 2)
        return_wizard = self.env["stock.return.picking"].create(
            {
                "picking_id": picking.id,
            }
        )
        return_wizard._onchange_picking_id()
        product_pack_return_move = return_wizard.product_return_moves.filtered(
            lambda m: m.product_id == self.product_pack
        )
        components_return_moves = return_wizard.product_return_moves.filtered(
            lambda m: m.product_id != self.product_pack
        )
        for components_return_move in components_return_moves:
            self.assertEqual(components_return_move.quantity, 2)
            components_return_move.write(
                {
                    "quantity": 99,
                    "to_refund": True,
                }
            )
            return_wizard._onchange_product_return_moves()
            self.assertIsNot(product_pack_return_move.quantity, 99)
        self.assertEqual(product_pack_return_move.quantity, 2)
        product_pack_return_move.quantity = 1
        return_wizard._onchange_product_return_moves()
        for components_return_move in components_return_moves:
            self.assertEqual(components_return_move.quantity, 1)
        picking_id = return_wizard.create_returns()["res_id"]
        picking_return_return = self.env["stock.picking"].browse(picking_id)
        moves = picking_return_return.move_ids
        for move in moves:
            self.assertEqual(move.product_uom_qty, 1)
