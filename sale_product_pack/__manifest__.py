# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale product Pack",
    "version": "13.0.1.0.1",
    "category": "Sales",
    "summary": "This module allows you to sale product packs",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, ADHOC SA, Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": ["product_pack", "sale"],
    "data": ["security/ir.model.access.csv", "views/product_pack_line_views.xml"],
    "demo": ["demo/product_pack_line_demo.xml"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
