# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Pos Product Pack",
    "summary": """
        Allows to sell product packs on POS sessions""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["rousseldenis"],
    "website": "https://github.com/OCA/product-pack",
    "depends": [
        "product_pack",
        "point_of_sale",
    ],
    "data": [
        "views/pos_product_pack.xml",
    ],
}
