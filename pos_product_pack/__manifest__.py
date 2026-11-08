# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Pos Product Pack",
    "summary": """
        Allows to sell product packs on POS sessions""",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["rousseldenis"],
    "website": "https://github.com/OCA/product-pack",
    "depends": [
        "product_pack",
        "point_of_sale",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_product_pack/static/src/js/order.esm.js",
            "pos_product_pack/static/src/js/order_line.esm.js",
            "pos_product_pack/static/src/js/store.esm.js",
            "pos_product_pack/static/src/css/pos_product_pack.css",
        ],
    },
}
