# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import ProductPackCommon


class TestProductPack(ProductPackCommon, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_product_pack_recursion(self):
        # Add pack product in its pack lines
        # Check constraint raises
        with self.assertRaises(ValidationError):
            self.cpu_detailed.write(
                {
                    "pack_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.cpu_detailed.id,
                                "quantity": 1.0,
                            },
                        )
                    ]
                }
            )

    @mute_logger("odoo.sql_db")
    def test_product_in_pack_unique(self):
        # Add product that is already in the concerned pack
        # Check constraint raises
        product_line = self.env.ref("product.product_product_16")
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.cpu_detailed.write(
                {
                    "pack_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product_line.id,
                                "quantity": 1.0,
                            },
                        )
                    ]
                }
            )

    def test_get_pack_line_price(self):
        # Check pack line price from product one
        component = self.env.ref("product_pack.pack_cpu_detailed_components_1")
        component.product_id.list_price = 30.0
        self.assertEqual(
            30.0,
            self.cpu_detailed.pack_line_ids.filtered(
                lambda cmp: cmp.product_id == component.product_id
            )._pack_line_price_compute("list_price")[component.product_id.id],
        )

    def test_get_pack_lst_price(self):
        # Check pack lst_price if totalized from components
        pack = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        component_1 = self.env.ref("product_pack.pack_cpu_detailed_totalized_1")
        component_1.product_id.list_price = 30.0
        component_2 = self.env.ref("product_pack.pack_cpu_detailed_totalized_3")
        component_2.product_id.list_price = 15.0
        component_3 = self.env.ref("product_pack.pack_cpu_detailed_components_4")
        component_3.product_id.list_price = 5.0
        self.assertEqual(50.0, pack.lst_price)

    def test_pack_company(self):
        # Try to assign pack lines with product that do not belong to pack
        # company
        component = self.env.ref("product_pack.pack_cpu_detailed_totalized_1")
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            component.product_id.company_id = self.company_2

    def test_pack_line_company(self):
        # Try to assign pack lines with product that do not belong to pack
        # company
        pack = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            pack.company_id = self.company_2

    def test_pack_type(self):
        # Change pack type from detailed to non detailed
        pack = self.env.ref(
            "product_pack.product_pack_cpu_detailed_components"
        ).product_tmpl_id
        pack.pack_modifiable = True
        with Form(pack) as pack_form:
            pack_form.pack_type = "non_detailed"
        self.assertFalse(pack_form.pack_modifiable)

    def test_pack_modifiable(self):
        # Pack is detailed with component price as detailed
        # Pack modifiable invisible should be False
        # Set the Pack as non detailed
        # Pack modifiable invisible should be True
        # Set the Pack as detailed with component price as totalized
        # Pack modifiable invisible should be True
        pack = self.env.ref(
            "product_pack.product_pack_cpu_detailed_components"
        ).product_tmpl_id
        self.assertFalse(pack.pack_modifiable_invisible)
        pack.pack_type = "non_detailed"
        self.assertTrue(pack.pack_modifiable_invisible)
        pack.pack_type = "detailed"
        pack.pack_component_price = "totalized"
        self.assertTrue(pack.pack_modifiable_invisible)

    def test_pack_price_with_pricelist_context(self):
        # Apply pricelist by context only for product packs (no components)

        # Pack Detailed
        pack = self.env.ref("product_pack.product_pack_cpu_detailed_components")
        price = pack.with_context(
            whole_pack_price=True, pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 2601.675)

        # Pack Totalized
        pack = self.env.ref("product_pack.product_pack_cpu_detailed_totalized")
        price = pack.with_context(
            pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 2574.0)

        # Pack Ignored
        pack = self.env.ref("product_pack.product_pack_cpu_detailed_ignored")
        price = pack.with_context(
            pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 27.675)

        # Pack Non detailed
        pack = self.env.ref("product_pack.product_pack_cpu_non_detailed")
        price = pack.with_context(
            pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 2574.0)
