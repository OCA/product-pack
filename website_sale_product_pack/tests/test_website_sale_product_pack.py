# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import HttpCase, tagged

from odoo.addons.website_sale.tests.common import MockRequest


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

    def test_shop_price_with_pricelist_without_rules(self):
        """The shop price of a pack adds up its components even when the website
        pricelist has no rules.

        A totalized pack keeps a symbolic sale price, so falling back to it shows a
        price that has nothing to do with what the customer pays.
        """
        component = self.env["product.product"].create(
            {
                "name": "Component without taxes",
                "list_price": 250.0,
                "is_published": True,
                "taxes_id": False,
            }
        )
        pack = self.env["product.template"].create(
            {
                "name": "Totalized pack with a symbolic sale price",
                "list_price": 1.0,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "totalized",
                "is_published": True,
                "taxes_id": False,
            }
        )
        self.env["product.pack.line"].create(
            {
                "parent_product_id": pack.product_variant_id.id,
                "product_id": component.id,
                "quantity": 2,
            }
        )
        website = self.env["website"].get_current_website()
        with MockRequest(self.env, website=website) as request:
            self.assertFalse(request.pricelist.item_ids)
            prices = pack._get_sales_prices(website)
            combination_info = pack._get_combination_info(only_template=True)
        self.assertEqual(prices[pack.id]["price_reduce"], 500.0)
        self.assertEqual(combination_info["price"], 500.0)

    def test_prevent_zero_price_sale_judges_whole_pack(self):
        """With the zero price sale prevention on, a pack whose main product is
        at 0 can be sold as long as the whole pack has a price."""
        website = self.env["website"].get_current_website()
        website.prevent_zero_price_sale = True
        website = website.with_user(self.user_portal)
        with MockRequest(website.env, website=website):
            for pack in self.packs.with_user(self.user_portal):
                combination_info = pack._get_combination_info(only_template=True)
                self.assertFalse(combination_info["prevent_zero_price_sale"], pack.name)
                variant = pack.product_variant_id
                self.assertTrue(variant._website_show_quick_add(), pack.name)
                self.assertTrue(variant._is_add_to_cart_allowed(), pack.name)
        for pack in self.packs:
            order = self.env["sale.order"].create(
                {
                    "partner_id": self.user_portal.partner_id.id,
                    "website_id": website.id,
                }
            )
            with MockRequest(self.env, website=website, sale_order_id=order.id):
                order._cart_add(product_id=pack.product_variant_id.id, quantity=1)
            self.assertTrue(order._is_cart_ready(), pack.name)

    def test_prevent_zero_price_sale_zero_priced_pack(self):
        """A pack whose whole price is 0 is still blocked."""
        website = self.env["website"].get_current_website()
        website.prevent_zero_price_sale = True
        component = self.env["product.product"].create(
            {"name": "Free component", "list_price": 0.0, "is_published": True}
        )
        pack = self.env["product.template"].create(
            {
                "name": "Pack without price",
                "list_price": 0.0,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "totalized",
                "is_published": True,
            }
        )
        self.env["product.pack.line"].create(
            {
                "parent_product_id": pack.product_variant_id.id,
                "product_id": component.id,
                "quantity": 1,
            }
        )
        order = self.env["sale.order"].create(
            {"partner_id": self.user_portal.partner_id.id, "website_id": website.id}
        )
        with MockRequest(self.env, website=website, sale_order_id=order.id):
            combination_info = pack._get_combination_info(only_template=True)
            self.assertTrue(combination_info["prevent_zero_price_sale"])
            with self.assertRaises(UserError):
                order._cart_add(product_id=pack.product_variant_id.id, quantity=1)

    def test_cart_notification_shows_the_whole_pack_price(self):
        """The notification of a pack whose components carry the price
        announces the price of the whole pack, not the zero of its main line."""
        component = self.env["product.product"].create(
            {
                "name": "Component of the notification pack",
                "list_price": 120.0,
                "is_published": True,
                "taxes_id": False,
            }
        )
        pack = self.env["product.template"].create(
            {
                "name": "Pack for the notification",
                "list_price": 0.0,
                "pack_ok": True,
                "pack_type": "detailed",
                "pack_component_price": "detailed",
                "is_published": True,
                "taxes_id": False,
            }
        )
        self.env["product.pack.line"].create(
            {
                "parent_product_id": pack.product_variant_id.id,
                "product_id": component.id,
                "quantity": 2,
            }
        )
        self.authenticate("portal_test", "portal_test")
        res = self.make_jsonrpc_request(
            "/shop/cart/add",
            {
                "product_template_id": pack.id,
                "product_id": pack.product_variant_id.id,
                "quantity": 1,
            },
        )
        lines = res["notification_info"]["lines"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["price_total"], 240.0)

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
