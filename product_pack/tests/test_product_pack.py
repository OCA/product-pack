# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo import Command, exceptions
from odoo.tests import Form
from odoo.tools import mute_logger

from .common import ProductPackCommon


class TestProductPack(ProductPackCommon):
    def test_product_pack_recursion(self):
        """Add pack product in its pack lines and check the constraint raises."""
        with self.assertRaises(exceptions.ValidationError):
            self.pack.pack_line_ids = [
                Command.create({"product_id": self.pack.id, "quantity": 1.0})
            ]

    @mute_logger("odoo.sql_db")
    def test_product_in_pack_unique(self):
        """Add product that is already in the pack and check the constraint raises."""
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.pack.pack_line_ids = [
                Command.create({"product_id": self.component1.id, "quantity": 1.0})
            ]

    def test_get_pack_line_price(self):
        # Check pack line price from product one
        self.component2.list_price = 30
        self.assertEqual(
            self.pack_line2._pack_line_price_compute("list_price")[self.component2.id],
            30,
        )

    def test_get_pack_lst_price(self):
        """Check pack lst_price if totalized from components."""
        self.pack.pack_component_price = "totalized"
        self.assertEqual(self.pack.lst_price, 70)

    def test_pack_company(self):
        """Try to assign pack lines with product that do not belong to pack company."""
        with self.assertRaises(exceptions.ValidationError), self.env.cr.savepoint():
            self.component1.company_id = self.company_2

    def test_pack_line_company(self):
        """Try to assign pack lines with product that do not belong to pack company."""
        with self.assertRaises(exceptions.ValidationError), self.env.cr.savepoint():
            self.pack.company_id = self.company_2

    def test_pack_type(self):
        """Change pack type from detailed to non detailed."""
        self.pack.pack_modifiable = True
        with Form(self.pack.product_tmpl_id) as pack_form:
            pack_form.pack_type = "non_detailed"
            self.assertFalse(pack_form.pack_modifiable)

    def test_pack_modifiable(self):
        # Pack is detailed with component price as detailed
        # Pack modifiable invisible should be False
        # Set the Pack as non detailed
        # Pack modifiable invisible should be True
        # Set the Pack as detailed with component price as totalized
        # Pack modifiable invisible should be True
        self.assertFalse(self.pack.pack_modifiable_invisible)
        self.pack.pack_type = "non_detailed"
        self.assertTrue(self.pack.pack_modifiable_invisible)
        self.pack.pack_type = "detailed"
        self.pack.pack_component_price = "totalized"
        self.assertTrue(self.pack.pack_modifiable_invisible)

    def test_pack_price_with_pricelist_context_detailed(self):
        price = self.pack.with_context(
            whole_pack_price=True, pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 72)  # 80 (10 + 70) with 10% discount

    def test_pack_price_with_pricelist_context_totalized(self):
        self.pack.pack_component_price = "totalized"
        price = self.pack.with_context(
            whole_pack_price=True, pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 63)  # 70 with 10% discount

    def test_pack_price_with_pricelist_context_ignored(self):
        self.pack.pack_component_price = "ignored"
        price = self.pack.with_context(
            whole_pack_price=True, pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 9)  # 10 with 10% discount

    def test_pack_price_with_pricelist_context_non_detailed(self):
        self.pack.pack_type = "non_detailed"
        price = self.pack.with_context(
            pricelist=self.discount_pricelist.id
        )._get_contextual_price()
        self.assertEqual(price, 63)  # 70 with 10% discount

    def test_pack_price_rule_totalized(self):
        """`_get_product_price_rule` must totalize components, as the e-commerce
        and the sales catalog build their prices with it."""
        self.pack.pack_component_price = "totalized"
        price, rule_id = self.discount_pricelist._get_product_price_rule(self.pack, 1.0)
        self.assertEqual(price, 63)  # 70 with 10% discount
        self.assertFalse(rule_id)  # no single rule explains a pack price

    def test_pack_price_rule_detailed(self):
        price, rule_id = self.discount_pricelist._get_product_price_rule(
            self.pack.with_context(whole_pack_price=True), 1.0
        )
        self.assertEqual(price, 72)  # 80 (10 + 70) with 10% discount
        self.assertFalse(rule_id)  # no single rule explains a pack price

    def test_pack_price_rule_ignored(self):
        """Not a pack to be handled: the pack's own price is used."""
        self.pack.pack_component_price = "ignored"
        price, rule_id = self.discount_pricelist._get_product_price_rule(self.pack, 1.0)
        self.assertEqual(price, 9)  # 10 with 10% discount
        self.assertEqual(rule_id, self.discount_pricelist.item_ids.id)

    def test_price_rule_no_pack(self):
        """Regular products must keep the standard behaviour."""
        price, rule_id = self.discount_pricelist._get_product_price_rule(
            self.component1, 1.0
        )
        self.assertEqual(price, 18)  # 20 with 10% discount
        self.assertEqual(rule_id, self.discount_pricelist.item_ids.id)

    def test_pack_price_rule_based_on_other_pricelist(self):
        """A pricelist based on another one must not add the components twice."""
        derived_pricelist = self.env["product.pricelist"].create(
            {
                "name": "Based on Discount",
                "company_id": self.env.company.id,
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "3_global",
                            "base": "pricelist",
                            "base_pricelist_id": self.discount_pricelist.id,
                            "compute_price": "formula",
                            "price_discount": 0,
                        },
                    )
                ],
            }
        )
        price, __ = derived_pricelist._get_product_price_rule(
            self.pack.with_context(whole_pack_price=True), 1.0
        )
        self.assertEqual(price, 72)  # 80 (10 + 70) with 10% discount, once
