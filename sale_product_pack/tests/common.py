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
        partner = cls.env["res.partner"].create(
            {
                "name": "Customer test",
                "email": "test@test.example.com",
                "phone": "+33 601 020 304",
                "street": "Rue de la mairie",
                "city": "New York",
                "zip": "97648",
                "website": "https://test.exemple.com",
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "company_id": cls.env.company.id,
                "partner_id": partner.id,
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
