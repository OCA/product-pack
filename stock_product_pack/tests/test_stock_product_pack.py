# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - João Marques
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests import Form, TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleProductPack(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_all_id = cls.env.ref("product.product_category_all").id
        cls.product_obj = cls.env["product.product"]
        cls.stock_rule_obj = cls.env["stock.rule"]
        cls.component_1 = cls.product_obj.create(
            {
                "name": "Component 1",
                "detailed_type": "product",
                "categ_id": cls.category_all_id,
            }
        )
        cls.component_2 = cls.product_obj.create(
            {
                "name": "Component 2",
                "detailed_type": "product",
                "categ_id": cls.category_all_id,
            }
        )
        cls.component_3 = cls.product_obj.create(
            {
                "name": "Component 3",
                "detailed_type": "service",
                "categ_id": cls.category_all_id,
            }
        )
        cls.component_4 = cls.product_obj.create(
            {
                "name": "Component 4",
                "detailed_type": "consu",
                "categ_id": cls.category_all_id,
            }
        )
        cls.pack_dc = cls.product_obj.create(
            {
                "name": "Pack",
                "detailed_type": "product",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": cls.category_all_id,
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
                    (
                        0,
                        0,
                        {"product_id": cls.component_3.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.component_4.id, "quantity": 1},
                    ),
                ],
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.user.id)], limit=1
        )
        cls.stock_rule = cls.stock_rule_obj.create(
            {
                "name": "Stock to Costumers",
                "action": "pull",
                "picking_type_id": cls.env.ref("stock.picking_type_internal").id,
                "route_id": cls.env.ref("stock.route_warehouse0_mto").id,
                "procure_method": "make_to_stock",
                "warehouse_id": cls.warehouse.id,
                "location_dest_id": cls.env.ref("stock.stock_location_stock").id,
            }
        )
        cls.pack_dc_with_dm = cls.product_obj.create(
            {
                "name": "Pack With storeable and not move product",
                "detailed_type": "product",
                "pack_ok": True,
                "dont_create_move": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": cls.category_all_id,
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
                    (
                        0,
                        0,
                        {"product_id": cls.component_3.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.component_4.id, "quantity": 1},
                    ),
                ],
            }
        )

    def test_compute_quantities_dict(self):
        location_id = (self.env.ref("stock.stock_location_suppliers").id,)
        location_dest_id = (self.env.ref("stock.stock_location_stock").id,)
        components = self.pack_dc.pack_line_ids.mapped("product_id")

        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.env.ref("base.res_partner_4").id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": location_id,
                "location_dest_id": location_dest_id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "incoming_move_test_01",
                            "product_id": components[0].id,
                            "product_uom_qty": 5,
                            "product_uom": components[0].uom_id.id,
                            "location_id": location_id,
                            "location_dest_id": location_dest_id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "incoming_move_test_02",
                            "product_id": components[1].id,
                            "product_uom_qty": 7,
                            "product_uom": components[1].uom_id.id,
                            "location_id": location_id,
                            "location_dest_id": location_dest_id,
                        },
                    ),
                ],
            }
        )
        picking.action_confirm()
        self.assertEqual(self.pack_dc.virtual_available, 5)
        self.assertEqual(self.pack_dc.qty_available, 0)
        wizard_dict = picking.button_validate()
        wizard = Form(
            self.env[(wizard_dict.get("res_model"))].with_context(
                **wizard_dict["context"]
            )
        ).save()
        wizard.process()
        self.assertEqual(self.pack_dc.virtual_available, 5)
        self.assertEqual(self.pack_dc.qty_available, 5)

    def test_pack_with_dont_move_the_parent(self):
        """Run a procurement for prod pack products when there are only 5 in stock then
        check that MTO is applied on the moves when the rule is set to 'mts_else_mto'
        """

        def create_orderpoint(product, qty_min, qty_max, location, group):
            return self.env["stock.warehouse.orderpoint"].create(
                {
                    "name": "OP/%s" % product.name,
                    "product_id": product.id,
                    "product_min_qty": qty_min,
                    "product_max_qty": qty_max,
                    "location_id": location.id,
                    "group_id": group.id,
                }
            )

        pg = self.env["procurement.group"].create({"name": "Test-product Pack"})
        create_orderpoint(
            self.pack_dc_with_dm,
            10,
            155,
            self.env.ref("stock.stock_location_stock"),
            pg,
        )
        self.env["stock.scheduler.compute"].create({}).procure_calculation()
        picking_ids = self.env["stock.picking"].search([("group_id", "=", pg.id)])
        # we need to ensure that only the compents of the packs are in the moves.
        self.assertFalse(self.pack_dc_with_dm in picking_ids.move_ids.product_id)

    def _create_stock_quant(self, product, qty):
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": qty,
            }
        )

    def test_picking_pack_consu(self):
        partner = self.env["res.partner"].create({"name": "Test partner"})
        pack = self.product_obj.create(
            {
                "name": "Pack (consumable)",
                "detailed_type": "consu",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": self.category_all_id,
                "pack_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": self.component_1.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": self.component_2.id, "quantity": 1},
                    ),
                ],
            }
        )
        self._create_stock_quant(self.component_1, 1)
        self._create_stock_quant(self.component_2, 1)
        picking_form = Form(
            self.env["stock.picking"].with_context(
                default_picking_type_id=self.warehouse.out_type_id.id,
                default_partner_id=partner.id,
            )
        )
        for product in [pack, self.component_1, self.component_2]:
            with picking_form.move_ids_without_package.new() as line_form:
                line_form.product_id = product
                line_form.product_uom_qty = 1
        picking = picking_form.save()
        # Order moves, when they are created from a sale order they already have
        # the correct consecutive sequence
        c1_move = picking.move_ids.filtered(lambda x: x.product_id == self.component_1)
        c1_move.sequence = 11
        c2_move = picking.move_ids.filtered(lambda x: x.product_id == self.component_2)
        c2_move.sequence = 12
        picking.action_confirm()
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
