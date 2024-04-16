# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Sale Product Pack",
    "category": "E-Commerce",
    "summary": "Compatibility module of product pack with e-commerce",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "depends": ["website_sale", "sale_product_pack"],
    "data": ["views/templates.xml"],
    "assets": {
        "web.assets_tests": [
            "website_sale_product_pack/static/src/js/website_sale_product_pack_tour.js",
        ],
    },
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-pack",
    "installable": True,
}
