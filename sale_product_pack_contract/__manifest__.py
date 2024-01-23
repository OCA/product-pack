# Copyright 2023 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Product Pack Contract",
    "version": "14.0.1.0.0",
    "category": "Sales",
    "summary": "Glue module between sale product pack and product.",
    "website": "https://github.com/OCA/product-pack",
    "author": (
        "Pierre Verkest <pierreverkest84@gmail.com>, "
        "Odoo Community Association (OCA),"
    ),
    "maintainers": ["petrus-v"],
    "license": "AGPL-3",
    "depends": ["sale_product_pack", "product_contract"],
    "data": [],
    "demo": [
        "demo/product_product_demo.xml",
    ],
    "installable": True,
}
