# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Product Pack",
    "version": "17.0.2.0.0",
    "category": "Sales",
    "summary": "This module allows you to sell product packs",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, ADHOC SA, Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["victoralmau"],
    "license": "AGPL-3",
    "depends": ["product_pack", "sale"],
    "data": ["security/ir.model.access.csv", "views/product_pack_line_views.xml"],
    "demo": [
        "demo/product_pack_line_demo.xml",
        "demo/sale_pack_demo.xml",
    ],
    "installable": True,
}
