# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Product Pack Line Modification",
    "summary": """
        Allows to modify a product pack line on sale order line""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-pack",
    "depends": [
        "sale_product_pack",
    ],
    "data": [
        "security/security.xml",
        "views/sale_order.xml",
        "wizards/sale_product_pack_line_modification.xml",
    ],
}
