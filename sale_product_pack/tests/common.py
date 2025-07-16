# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command

from odoo.addons.product_pack.tests.common import ProductPackCommon


class TestSaleProductPackBase(ProductPackCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test",
                "company_id": cls.env.company.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
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
        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": cls.env.ref("base.res_partner_12").id,
                "pricelist_id": pricelist.id,
            }
        )

    def _add_so_line(self, product=None, sequence=10):
        product = product or self.pack
        return self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 1,
                "sequence": sequence,
            }
        )
