# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestProductPackCategoryRestriction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_product = cls.env["product.product"]
        cls.product_category = cls.env["product.category"]

        cls.categ_test = cls.product_category.create(
            {"name": "Test Category 1", "pack_ok": True}
        )
        cls.categ_test2 = cls.product_category.create(
            {"name": "Test Category 2", "pack_ok": False}
        )
        cls.product_pack = cls.product_product.create(
            {
                "name": "Test Product 1",
                "categ_id": cls.categ_test.id,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
            }
        )
        cls.product_no_pack = cls.product_product.create(
            {"name": "Test Product 2", "categ_id": cls.categ_test2.id}
        )

    def test_product_pack_ok(self):
        """
        - User tries to mark product as pack when it is not part of a pack
          product category.

        - User tries to create a new pack product for a non pack category.
        """
        with self.assertRaises(ValidationError):
            self.product_no_pack.write({"pack_ok": True})
        with self.assertRaises(ValidationError):
            self.product_product.create(
                {
                    "name": "Test Product 3",
                    "pack_ok": True,
                    "pack_type": "detailed",
                    "pack_component_price": "detailed",
                    "categ_id": self.categ_test2.id,
                }
            )

    def test_category_pack_ok(self):
        """User tries to change pack category to non pack category but there are
        pack products assigned to it."""
        with self.assertRaises(ValidationError):
            self.categ_test.write({"pack_ok": False})
