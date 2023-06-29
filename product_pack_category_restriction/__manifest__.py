# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product Pack Category Restriction",
    "version": "13.0.1.0.0",
    "category": "Product",
    "summary": """
        This module allows you to restrict pack products to specific Product
        Categories.
    """,
    "website": "https://github.com/OCA/product-pack",
    "author": "ForgeFlow,Odoo Community Association (OCA)",
    "maintainers": ["JordiMForgeFlow"],
    "license": "AGPL-3",
    "depends": ["product_pack"],
    "data": ["views/product_category_views.xml"],
    "installable": True,
    "application": False,
}
