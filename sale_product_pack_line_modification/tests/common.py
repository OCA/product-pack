# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import TransactionCase


class SaleProductPackLineModificationCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modif_wizard_obj = cls.env["sale.product.pack.line.modification"]
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Replacement Product",
            }
        )
        cls.component_1 = cls.env["product.product"].create(
            {
                "name": "Pack Component 1",
            }
        )
        cls.component_2 = cls.env["product.product"].create(
            {
                "name": "Pack Component 2",
            }
        )
        cls.component_3 = cls.env["product.product"].create(
            {
                "name": "Pack Component 3",
            }
        )
        cls.product_cp = cls.env["product.product"].create(
            {
                "name": "Ignored Detailed Pack",
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "ignored",
                "pack_modifiable": True,
                "pack_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.component_1.id,
                            "quantity": 1.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.component_2.id,
                            "quantity": 1.0,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.component_3.id,
                            "quantity": 1.0,
                        }
                    ),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test",
                "company_id": cls.env.company.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        }
                    )
                ],
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": cls.partner.id,
                "pricelist_id": cls.pricelist.id,
            }
        )
