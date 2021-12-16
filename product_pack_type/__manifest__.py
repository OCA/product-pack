# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Pack Type",
    "summary": """
        Allows to define a type on product which is a pack""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-pack",
    "depends": [
        "product_pack",
    ],
    "data": [
        "security/product_pack_type.xml",
        "views/product_pack_type.xml",
        "views/product_template.xml",
    ],
    "demo": [
        "demo/product_pack_type.xml",
        "demo/product_product.xml",
    ],
}
