# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase

from odoo.addons.product_pack.tests.common import ProductPackCommon


class TestProductPack(ProductPackCommon, SavepointCase):
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

    def test_product_pack_type_count(self):
        pack_type = self._create_type()
        self.assertEqual(0, pack_type.product_pack_count)
        self.cpu_detailed.pack_type_id = pack_type
        self.cpu_detailed.invalidate_cache()
        self.assertEqual(1, pack_type.product_pack_count)
