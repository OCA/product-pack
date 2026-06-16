# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Product Pack",
    "version": "18.0.1.1.0",
    "category": "Sales",
    "summary": "This module allows you to sell product packs",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, ADHOC SA, Tecnativa, ACSONE SA/NV,"
    " Odoo Community Association (OCA)",
    "maintainers": ["victoralmau"],
    "license": "AGPL-3",
    "depends": ["product_pack", "sale"],
    "data": ["security/ir.model.access.csv", "views/product_pack_line_views.xml"],
    "demo": [
        "demo/product_pack_line_demo.xml",
        "demo/sale_pack_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_product_pack/static/src/js/**/*.js",
        ],
        "web.assets_unit_tests": [
            "sale_product_pack/static/tests/sale_order_line.esm.test.js",
        ],
    },
    "installable": True,
}
