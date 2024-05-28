# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Purchase Product Pack",
    "version": "17.0.1.0.0",
    "category": "Purchase",
    "summary": "This module allows you to buy product packs",
    "website": "https://github.com/OCA/product-pack",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["product_pack", "purchase"],
    "data": ["security/ir.model.access.csv", "views/product_pack_line_views.xml"],
    "demo": [],
    "installable": True,
}
