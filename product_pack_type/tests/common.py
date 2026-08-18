# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.product_pack.tests.common import ProductPackCommon


class ProductPackTypeCommon(ProductPackCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pack_type_obj = cls.env["product.pack.type"]

    @classmethod
    def _create_type(cls, vals=None):
        if not vals:
            vals = {}
        vals.update({"name": "CPUs"})
        return cls.pack_type_obj.create(vals)
