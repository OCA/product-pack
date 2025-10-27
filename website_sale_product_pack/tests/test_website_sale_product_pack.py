# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class WebsiteSaleHttpCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create portal user
        cls.user_portal = cls.env["res.users"].create(
            {
                "name": "Portal User Test",
                "login": "portal_test",
                "email": "portal@test.com",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )

        # Create component products
        cls.component_1 = cls.env["product.product"].create(
            {
                "name": "Component 1",
                "list_price": 100.0,
                "is_published": True,
                "website_sequence": 10,
            }
        )
        cls.component_2 = cls.env["product.product"].create(
            {
                "name": "Component 2",
                "list_price": 200.0,
                "is_published": True,
                "website_sequence": 11,
            }
        )
        cls.component_3 = cls.env["product.product"].create(
            {
                "name": "Component 3",
                "list_price": 50.0,
                "is_published": True,
                "website_sequence": 12,
            }
        )

        # Create pack products
        cls.product_pdc = cls.env["product.template"].create(
            {
                "name": "Pack CPU (Detailed - Displayed Components Price)",
                "list_price": 0.0,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "is_published": True,
                "website_sequence": 0,
            }
        )
        cls.env["product.pack.line"].create(
            [
                {
                    "parent_product_id": cls.product_pdc.product_variant_id.id,
                    "product_id": cls.component_1.id,
                    "quantity": 1,
                },
                {
                    "parent_product_id": cls.product_pdc.product_variant_id.id,
                    "product_id": cls.component_2.id,
                    "quantity": 2,
                },
                {
                    "parent_product_id": cls.product_pdc.product_variant_id.id,
                    "product_id": cls.component_3.id,
                    "quantity": 1,
                },
            ]
        )

        cls.product_pdi = cls.env["product.template"].create(
            {
                "name": "Pack CPU (Detailed - Ignored Components Price)",
                "list_price": 30.75,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "ignored",
                "is_published": True,
                "website_sequence": 1,
            }
        )
        cls.env["product.pack.line"].create(
            [
                {
                    "parent_product_id": cls.product_pdi.product_variant_id.id,
                    "product_id": cls.component_1.id,
                    "quantity": 1,
                },
                {
                    "parent_product_id": cls.product_pdi.product_variant_id.id,
                    "product_id": cls.component_2.id,
                    "quantity": 1,
                },
                {
                    "parent_product_id": cls.product_pdi.product_variant_id.id,
                    "product_id": cls.component_3.id,
                    "quantity": 1,
                },
            ]
        )

        cls.product_pdt = cls.env["product.template"].create(
            {
                "name": "Pack CPU (Detailed - Totalized Components Price)",
                "list_price": 0.0,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "totalized",
                "is_published": True,
                "website_sequence": 2,
            }
        )
        cls.env["product.pack.line"].create(
            [
                {
                    "parent_product_id": cls.product_pdt.product_variant_id.id,
                    "product_id": cls.component_1.id,
                    "quantity": 2,
                    "sale_discount": 15.0,
                },
                {
                    "parent_product_id": cls.product_pdt.product_variant_id.id,
                    "product_id": cls.component_2.id,
                    "quantity": 5,
                    "sale_discount": 10.0,
                },
                {
                    "parent_product_id": cls.product_pdt.product_variant_id.id,
                    "product_id": cls.component_3.id,
                    "quantity": 10,
                },
            ]
        )

        cls.product_pnd = cls.env["product.template"].create(
            {
                "name": "Non Detailed - Totalized Components Price",
                "list_price": 0.0,
                "pack_ok": True,
                "pack_type": "non_detailed",
                "pack_component_price": "totalized",
                "is_published": True,
                "website_sequence": 3,
            }
        )
        cls.env["product.pack.line"].create(
            [
                {
                    "parent_product_id": cls.product_pnd.product_variant_id.id,
                    "product_id": cls.component_1.id,
                    "quantity": 2,
                    "sale_discount": 15.0,
                },
                {
                    "parent_product_id": cls.product_pnd.product_variant_id.id,
                    "product_id": cls.component_2.id,
                    "quantity": 5,
                    "sale_discount": 10.0,
                },
                {
                    "parent_product_id": cls.product_pnd.product_variant_id.id,
                    "product_id": cls.component_3.id,
                    "quantity": 10,
                },
            ]
        )

        cls.packs = (
            cls.product_pdc + cls.product_pdi + cls.product_pdt + cls.product_pnd
        )

        # Create and select a specific pricelist
        website = cls.env["website"].get_current_website()
        pricelist = cls.env["product.pricelist"].create(
            {
                "name": "website_sale_product_pack public",
                "currency_id": website.company_id.currency_id.id,
                "selectable": True,
            }
        )
        cls.user_portal.property_product_pricelist = pricelist
        website.user_id.property_product_pricelist = pricelist
        admin = cls.env.ref("base.user_admin")
        admin.property_product_pricelist = pricelist

    def _get_component_prices_sum(self, product_pack):
        component_prices = 0.0
        for pack_line in product_pack.get_pack_lines():
            product_line_price = pack_line.product_id.list_price * (
                1 - (pack_line.sale_discount or 0.0) / 100.0
            )
            component_prices += product_line_price * pack_line.quantity
        return component_prices

    def test_create_components_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a
        frontend tour"""
        self.start_tour(
            "/shop", "create_components_price_order_line", login="portal_test"
        )
        sale = self.env["sale.order"].search([], limit=1, order="id desc")
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        product_variant = self.product_pdc.product_variant_id
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            product_variant | product_variant.get_pack_lines().mapped("product_id"),
        )

    def test_create_ignored_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend
        tour"""
        self.start_tour("/shop", "create_ignored_price_order_line", login="portal_test")
        sale = self.env["sale.order"].search([], limit=1, order="id desc")
        product_variant = self.product_pdi.product_variant_id
        line = sale.order_line.filtered(lambda x: x.product_id == product_variant)
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            product_variant | product_variant.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual((sale.order_line - line).mapped("price_subtotal"), [0, 0, 0])
        # Pack price is different from the sum of component prices
        self.assertEqual(line.price_subtotal, 30.75)
        self.assertNotEqual(self._get_component_prices_sum(product_variant), 30.75)

    def test_create_totalized_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend tour
        with a detailed totalized pack"""
        self.start_tour(
            "/shop", "create_totalized_price_order_line", login="portal_test"
        )
        sale = self.env["sale.order"].search([], limit=1, order="id desc")
        product_variant = self.product_pdt.product_variant_id
        line = sale.order_line.filtered(lambda x: x.product_id == product_variant)
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            product_variant | product_variant.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual((sale.order_line - line).mapped("price_subtotal"), [0, 0, 0])
        # Pack price is equal to the sum of component prices
        # Component 1: 100 * 2 * (1 - 0.15) = 170.0
        # Component 2: 200 * 5 * (1 - 0.10) = 900.0
        # Component 3: 50 * 10 = 500.0
        # Total: 1570.0
        self.assertEqual(line.price_subtotal, 1570.0)
        self.assertEqual(self._get_component_prices_sum(product_variant), 1570.0)

    def test_create_non_detailed_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend
        tour"""
        self.start_tour(
            "/shop", "create_non_detailed_price_order_line", login="portal_test"
        )
        sale = self.env["sale.order"].search([], limit=1, order="id desc")
        product_variant = self.product_pnd.product_variant_id
        line = sale.order_line.filtered(lambda x: x.product_id == product_variant)
        # After create, there will be only one line, because product_type is
        # set to 'non_detailed'
        self.assertEqual(len(sale.order_line), 1)
        # After create, there will be only one line, because product_type is
        # set to 'non_detailed'
        self.assertEqual(line.product_id, product_variant)
        # Pack price is equal to the sum of component prices
        # Component 1: 100 * 2 * (1 - 0.15) = 170.0
        # Component 2: 200 * 5 * (1 - 0.10) = 900.0
        # Component 3: 50 * 10 = 500.0
        # Total: 1570.0
        self.assertEqual(line.price_subtotal, 1570.0)
        self.assertEqual(self._get_component_prices_sum(product_variant), 1570.0)

    def test__check_to_add_pack_component_pusblished(self):
        """
        Test when create a product pack with only published products as components.
        """
        with self.assertRaises(ValidationError):
            # Create an unpublished product
            unpublished_component = self.env["product.product"].create(
                {
                    "name": "Unpublished Component",
                    "list_price": 50.0,
                    "is_published": False,
                }
            )
            vals = {
                "product_id": unpublished_component.id,
                "parent_product_id": self.product_pdc.product_variant_id.id,
            }
            pack_line = self.env["product.pack.line"].create(vals)
            self.product_pdc.write({"pack_line_ids": [(4, pack_line.id)]})
