# Copyright 2021 ACSONE SA/NV
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command
from odoo.tests import TransactionCase


class ProductPackCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.product_pack_line_obj = cls.env["product.pack.line"]
        cls.component1 = cls.env["product.product"].create(
            {"name": "Pack component 1", "list_price": 20, "company_id": cls.company.id}
        )
        cls.component2 = cls.env["product.product"].create(
            {"name": "Pack component 2", "list_price": 30, "company_id": cls.company.id}
        )
        cls.pack = cls.env["product.product"].create(
            {
                "name": "Test product pack",
                "company_id": cls.company.id,
                "type": "service",
                "list_price": 10,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "pack_line_ids": [
                    Command.create({"product_id": cls.component1.id, "quantity": 2}),
                    Command.create({"product_id": cls.component2.id, "quantity": 1}),
                ],
            }
        )
        cls.pack_line1 = cls.pack.pack_line_ids[0]
        cls.pack_line2 = cls.pack.pack_line_ids[1]
        cls.company_2 = cls.env["res.company"].create({"name": "Company Pack 2"})
        cls.discount_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Discount",
                "company_id": cls.env.company.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "percentage",
                            "percent_price": 10,
                        },
                    )
                ],
            }
        )
