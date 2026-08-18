# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from .common import ProductPackTypeCommon


class TestProductPack(ProductPackTypeCommon, TransactionCase):
    def test_product_pack_type_count(self):
        # Create a pack type
        # Affect a pack product to that type
        # Check count
        pack_type = self._create_type()
        self.assertEqual(0, pack_type.product_pack_count)
        self.pack.product_tmpl_id.pack_type_id = pack_type
        pack_type.invalidate_recordset()
        self.assertEqual(1, pack_type.product_pack_count)
