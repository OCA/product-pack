# Copyright 2021 Tecnativa - David Vidal
# Copyright 2025 Tecnativa - Pedro M. Baeza
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.sale_product_pack.tests.common import TestSaleProductPackBase


class TestSaleStockProductPack(TestSaleProductPackBase):
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
        key_0 = list(sol_data.keys())[0]
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
            lambda x: x.pack_parent_line_id == sol_pack
            and x.product_id == self.component1
        )
        sol_pack_component2 = self.sale_order.order_line.filtered(
            lambda x: x.pack_parent_line_id == sol_pack
            and x.product_id == self.component2
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

    def test_dont_create_move_non_detailed_pack(self):
        """A 'Non Detailed' pack with 'dont_create_move' active must not
        generate a stock.move for the parent product either.
        Regression test for stock_rule.run(), which used to only skip the
        parent procurement when pack_type == 'detailed', silently ignoring
        the flag for non detailed packs.

        qty_delivered is left untouched: it stays driven by real stock
        moves, so a pack that moves nothing is simply not delivered. Such a
        pack shouldn't be invoiced on delivery in the first place -- that
        is what invoice_policy is for.
        """
        self.pack.write(
            {
                "pack_type": "non_detailed",
                "dont_create_move": True,
            }
        )
        pack_line = self._add_so_line()
        self.sale = self.sale_order
        self.sale.action_confirm()
        self.assertFalse(
            self.sale.picking_ids.move_ids.filtered(
                lambda move: move.product_id == self.pack
            ),
            "The pack product must not generate a stock.move when "
            "'dont_create_move' is active, regardless of its pack display "
            "type.",
        )
        self.assertEqual(
            pack_line.qty_delivered,
            0.0,
            "Confirming the order must not mark the pack as delivered: "
            "qty_delivered has to reflect real stock moves only.",
        )

    def test_enabling_dont_create_move_keeps_delivery_history(self):
        """Enabling 'dont_create_move' on a product must not rewrite the
        delivered quantity of orders that were already (partially)
        delivered.

        Regression test for the scenario reported in review: sell 4 packs
        with the flag disabled, deliver 2, then enable the flag ->
        qty_delivered used to jump from 2 to 4, altering delivery history
        and risking over-invoicing.
        """
        self.pack.pack_type = "non_detailed"
        pack_line = self._add_so_line()
        pack_line.product_uom_qty = 4
        self.sale_order.action_confirm()
        # Deliver 2 out of the 4 ordered packs.
        pack_move = self.sale_order.picking_ids.move_ids.filtered(
            lambda move: move.product_id == self.pack
        )
        self.assertTrue(pack_move, "The pack should move while the flag is off.")
        pack_move.quantity = 2
        pack_move.picked = True
        pack_move.picking_id._action_done()
        self.assertEqual(pack_line.qty_delivered, 2.0)

        self.pack.dont_create_move = True

        self.assertEqual(
            pack_line.qty_delivered,
            2.0,
            "Enabling 'dont_create_move' must not restate what was already delivered.",
        )

    def _create_return_moves(self, delivery_moves, qty_by_product):
        # Return moves are created directly via the ORM (state='done',
        # to_refund=True) instead of going through stock.picking /
        # stock.return.picking: that orchestration depends on the
        # warehouse's delivery route (one-step vs multi-step) and on
        # enterprise overrides (e.g. helpdesk_stock redeclares the wizard's
        # 'picking_id' as a computed field with unrelated resolution
        # logic), both of which make it fragile and environment-dependent
        # for a unit test. This mirrors exactly the fields
        # _compute_qty_delivered's filter looks at.
        return_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": delivery_moves[:1].picking_id.picking_type_id.id,
                "location_id": delivery_moves[:1].location_dest_id.id,
                "location_dest_id": delivery_moves[:1].location_id.id,
            }
        )
        for move in delivery_moves:
            qty = qty_by_product.get(move.product_id, 0.0)
            if not qty:
                continue
            self.env["stock.move"].create(
                {
                    "product_id": move.product_id.id,
                    "product_uom_qty": qty,
                    "quantity": qty,
                    "product_uom": move.product_uom.id,
                    "picking_id": return_picking.id,
                    "location_id": move.location_dest_id.id,
                    "location_dest_id": move.location_id.id,
                    "sale_line_id": move.sale_line_id.id,
                    "origin_returned_move_id": move.id,
                    "to_refund": True,
                    "state": "done",
                    "picked": True,
                }
            )
        return return_picking

    def test_qty_delivered_pack_after_component_return(self):
        """A detailed pack's own qty_delivered must drop when its
        components are returned, without any manual/forced recompute.

        Regression test for the missing @api.depends on
        _compute_qty_delivered: it derives the pack line's qty_delivered
        from its children's qty_delivered, but only depended on the pack
        line's own (untouched) stock moves, so returning the components
        never invalidated the cached value on the parent.
        """
        self.pack.pack_type = "detailed"
        self.component1.is_storable = True
        self.component2.is_storable = True
        pack_line = self._add_so_line(self.pack)
        pack_line.product_uom_qty = 2
        self._create_stock_quant(self.component1, 10)
        self._create_stock_quant(self.component2, 10)
        # Some Adhoc-only modules (sale_exception, not a dependency of this
        # OCA module) can silently turn action_confirm() into a no-op (it
        # returns a popup action instead of confirming) for a partner/order
        # that trips an exception rule, e.g. an unapproved partner. Mirror
        # the "Ignore Exceptions" checkbox so this test isn't at the mercy
        # of whatever exception rules happen to be configured wherever it
        # runs.
        if "ignore_exception" in self.sale_order._fields:
            self.sale_order.ignore_exception = True
        self.sale_order.action_confirm()
        self.assertEqual(
            self.sale_order.state, "sale", "action_confirm did not confirm the order."
        )
        picking = self.sale_order.picking_ids
        picking.button_validate()
        self.assertEqual(
            picking.state,
            "done",
            "Delivery picking did not complete (button_validate likely "
            "returned a wizard action instead of validating directly).",
        )

        self.assertEqual(pack_line.qty_delivered, 2.0)

        # Return exactly 1 pack's worth of both components (proportional).
        delivery_moves = picking.move_ids.filtered(lambda m: m.state == "done")
        self.assertTrue(delivery_moves, "No completed delivery moves found to return.")
        self._create_return_moves(
            delivery_moves, {self.component1: 2.0, self.component2: 1.0}
        )

        # No explicit invalidate/recompute call here: this must reflect the
        # return through normal field dependency tracking alone.
        self.assertEqual(pack_line.qty_delivered, 1.0)
