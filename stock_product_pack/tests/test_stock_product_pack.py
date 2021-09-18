# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests import Form, SavepointCase

_logger = logging.getLogger(__name__)


class TestSaleProductPack(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        category_all_id = cls.env.ref("product.product_category_all").id
        cls.product_obj = cls.env["product.product"]
        cls.stock_rule_obj = cls.env["stock.rule"]
        component_1 = cls.product_obj.create(
            {"name": "Component 1", "type": "product", "categ_id": category_all_id}
        )
        component_2 = component_1.with_context({}).copy({"name": "Component 2"})
        component_3 = component_1.with_context({}).copy(
            {"name": "Component 3", "type": "service"}
        )
        component_4 = component_1.with_context({}).copy(
            {"name": "Component 4", "type": "consu"}
        )
        cls.pack_dc = cls.product_obj.create(
            {
                "name": "Pack",
                "type": "product",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": category_all_id,
                "pack_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": component_1.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_2.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_3.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_4.id, "quantity": 1},
                    ),
                ],
            }
        )
        warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.user.id)], limit=1
        )
        cls.stock_rule = cls.stock_rule_obj.create(
            {
                "name": "Stock to Costumers",
                "action": "pull",
                "picking_type_id": cls.env.ref("stock.picking_type_internal").id,
                "route_id": cls.env.ref("stock.route_warehouse0_mto").id,
                "procure_method": "make_to_stock",
                "warehouse_id": warehouse.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
            }
        )
        cls.pack_dc_with_dm = cls.product_obj.create(
            {
                "name": "Pack With storeable and not move product",
                "type": "product",
                "pack_ok": True,
                "dont_create_move": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": category_all_id,
                "pack_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": component_1.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_2.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_3.id, "quantity": 1},
                    ),
                    (
                        0,
                        0,
                        {"product_id": component_4.id, "quantity": 1},
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
                "move_lines": [
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
                wizard_dict["context"]
            )
        ).save()
        wizard.process()
        self.product_obj.invalidate_cache()
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
        self.assertFalse(self.pack_dc_with_dm in picking_ids.move_lines.product_id)
