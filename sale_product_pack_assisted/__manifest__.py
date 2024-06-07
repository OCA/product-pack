# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Assisted Sale product Pack",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, ADHOC SA, Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["jjscarafia"],
    "license": "AGPL-3",
    "depends": ["sale_product_pack"],
    "data": [
        "views/sale_order_line_pack_line_views.xml",
        "views/sale_order_line_views.xml",
        "views/sale_order_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
