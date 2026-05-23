# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


class ProductPackCommon:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_pack_line_obj = cls.env["product.pack.line"]
        cls.cpu_detailed = cls.env.ref(
            "product_pack.product_pack_cpu_detailed_components"
        )
        vals = {
            "name": "Company Pack 2",
        }
        cls.company_2 = cls.env["res.company"].create(vals)
        cls.discount_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Discount",
                "company_id": cls.env.company.id,
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "percentage",
                            "percent_price": 10,
                        },
                    )
                ],
            }
        )
