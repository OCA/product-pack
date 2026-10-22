# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - João Marques
# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestStockProductPack(BaseCommon):
    # Odoo 20 runs each test as _test_user: these groups are the ones the
    # module's own access rules rely on.
    _test_user_groups = ("stock.group_stock_manager", "product.group_product_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a product category for testing instead of relying on demo data
        category = cls.env["product.category"].create(
            {
                "name": "Test Category",
            }
        )
        category_all_id = category.id
        cls.product_obj = cls.env["product.product"]
        # The model stock doesn't add anymore the 'product'
        # selection to the product type.
        # Thus the type is changed to 'consu'
        cls.component_1 = cls.product_obj.create(
            {
                "name": "Component 1",
                "type": "consu",
                "is_storable": True,
                "categ_id": category_all_id,
            }
        )
        cls.component_2 = cls.product_obj.create(
            {
                "name": "Component 2",
                "type": "consu",
                "is_storable": True,
                "categ_id": category_all_id,
            }
        )
        cls.component_3 = cls.product_obj.create(
            {
                "name": "Component 3",
                "type": "service",
                "categ_id": category_all_id,
            }
        )
        cls.component_4 = cls.product_obj.create(
            {
                "name": "Component 4",
                "type": "consu",
                "is_storable": True,
                "categ_id": category_all_id,
            }
        )
        cls.pack_dc = cls.product_obj.create(
            {
                "name": "Pack",
                "type": "consu",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": category_all_id,
                "pack_line_ids": [
                    Command.create(
                        {"product_id": cls.component_1.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_2.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_3.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_4.id, "quantity": 1},
                    ),
                ],
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.pack_dc_with_dm = cls.product_obj.create(
            {
                "name": "Pack With storeable and not move product",
                "type": "consu",
                "pack_ok": True,
                "dont_create_move": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "categ_id": category_all_id,
                "pack_line_ids": [
                    Command.create(
                        {"product_id": cls.component_1.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_2.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_3.id, "quantity": 1},
                    ),
                    Command.create(
                        {"product_id": cls.component_4.id, "quantity": 1},
                    ),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})

    def _create_picking(self, picking_type_id, moves_data):
        picking_form = Form(
            self.env["stock.picking"].with_context(
                default_picking_type_id=picking_type_id,
            )
        )
        picking_form.partner_id = self.partner
        for move_data in moves_data:
            with picking_form.move_ids.new() as move:
                move.product_id = move_data[0]
                move.product_uom_qty = move_data[1]
        return picking_form.save()

    def test_compute_quantities_dict(self):
        moves_data = [
            (self.component_1, 5),
            (self.component_2, 7),
            (self.component_4, 9),
        ]
        picking = self._create_picking(self.warehouse.in_type_id.id, moves_data)
        picking.action_confirm()
        self.assertEqual(self.pack_dc.virtual_available, 5)
        self.assertEqual(self.pack_dc.qty_available, 0)
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(self.pack_dc.virtual_available, 5)
        self.assertEqual(self.pack_dc.qty_available, 5)

    def _create_stock_quant(self, product, qty):
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": qty,
            }
        )

    def test_picking_pack_consu(self):
        # Simulate the out picking that would be generated
        self.pack_dc.pack_type = "detailed"
        self.component_1.is_storable = True
        self.component_2.is_storable = True
        self.component_3.is_storable = True
        self.component_4.is_storable = True
        self._create_stock_quant(self.component_1, 1)
        self._create_stock_quant(self.component_2, 1)
        self._create_stock_quant(self.component_3, 1)
        self._create_stock_quant(self.component_4, 1)
        moves_data = [
            (self.pack_dc, 1),
            (self.component_1, 1),
            (self.component_2, 1),
            (self.component_3, 1),
            (self.component_4, 1),
        ]
        picking = self._create_picking(self.warehouse.out_type_id.id, moves_data)
        picking.action_confirm()
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        data_names = []
        aggregated_lines = picking.move_line_ids._get_aggregated_product_quantities()
        for line in aggregated_lines:
            data_names.append(aggregated_lines[line]["name"])
        self.assertEqual(
            data_names,
            [
                "Pack",
                "Component 1",
                "Component 2",
                "Component 3",
                "Component 4",
            ],
        )

    def test_pack_with_dont_move_the_parent(self):
        """Run a procurement for prod pack products when there are only 5 in stock then
        check that MTO is applied on the moves when the rule is set to 'mts_else_mto'
        """

        def create_orderpoint(product, qty_min, qty_max, location):
            return self.env["stock.warehouse.orderpoint"].create(
                {
                    "name": f"OP/{product.name}",
                    "product_id": product.id,
                    "product_min_qty": qty_min,
                    "product_max_qty": qty_max,
                    "location_id": location.id,
                }
            )

        create_orderpoint(
            self.pack_dc_with_dm,
            10,
            155,
            self.warehouse.lot_stock_id,
        )
        # Check that no moves were created for the pack product itself
        # Only components should have moves created
        pack_moves = self.env["stock.move"].search(
            [("product_id", "=", self.pack_dc_with_dm.id)]
        )
        self.assertFalse(pack_moves)
