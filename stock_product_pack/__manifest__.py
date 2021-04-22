# Copyright 2021 Julio Cesar Bravo Rodriguez
# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2020 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock product Pack",
    "version": "14.0.1.0.1",
    "category": "Warehouse",
    "summary": "This module allows you to get the right available quantities "
    "of the packs",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, " "ADHOC SA, " "Tecnativa, " "Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": ["product_pack", "stock"],
    "data": ["security/ir.model.access.csv", "views/product_template_views.xml"],
    "installable": True,
    "auto_install": True,
    "application": False,
}
