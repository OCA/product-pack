# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class WebsiteSaleHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.user_portal = self.env.ref("base.demo_user0")
        self.product_pdc = self.env.ref(
            "product_pack.product_pack_cpu_detailed_components"
        )
        self.product_pdi = self.env.ref(
            "product_pack.product_pack_cpu_detailed_ignored"
        )
        self.product_pdt = self.env.ref(
            "product_pack.product_pack_cpu_detailed_totalized"
        )
        self.product_pnd = self.env.ref("product_pack.product_pack_cpu_non_detailed")
        self.packs = (
            self.product_pdc + self.product_pdi + self.product_pdt + self.product_pnd
        )
        # Publish the products and put them in the first results
        self.packs.write({"website_published": True, "website_sequence": 0})
        # Create and select a specific pricelist for avoiding problems in integrated
        # environments where the default pricelist currency has been changed
        website = self.env["website"].get_current_website()
        pricelist = self.env["product.pricelist"].create(
            {
                "name": "website_sale_product_pack public",
                "currency_id": website.user_id.company_id.currency_id.id,
                "selectable": True,
            }
        )
        self.user_portal.property_product_pricelist = pricelist
        website.user_id.property_product_pricelist = pricelist
        admin = self.env.ref("base.user_admin")
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
        self.start_tour("/shop", "create_components_price_order_line", login="portal")
        sale = self.env["sale.order"].search([], limit=1)
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            self.product_pdc | self.product_pdc.get_pack_lines().mapped("product_id"),
        )

    def test_create_ignored_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend
        tour"""
        self.start_tour("/shop", "create_ignored_price_order_line", login="portal")
        sale = self.env["sale.order"].search([], limit=1)
        line = sale.order_line.filtered(lambda x: x.product_id == self.product_pdi)
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            self.product_pdi | self.product_pdi.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual((sale.order_line - line).mapped("price_subtotal"), [0, 0, 0])
        # Pack price is different from the sum of component prices
        self.assertEqual(line.price_subtotal, 30.75)
        self.assertNotEqual(self._get_component_prices_sum(self.product_pdi), 30.75)

    def test_create_totalized_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend tour
        with a detailed totalized pack"""
        self.start_tour("/shop", "create_totalized_price_order_line", login="portal")
        sale = self.env["sale.order"].search([], limit=1)
        line = sale.order_line.filtered(lambda x: x.product_id == self.product_pdt)
        # After create, there will be four lines
        self.assertEqual(len(sale.order_line), 4)
        # The products of those four lines are the main product pack and its
        # product components
        self.assertEqual(
            sale.order_line.mapped("product_id"),
            self.product_pdt | self.product_pdt.get_pack_lines().mapped("product_id"),
        )
        # All component lines have zero as subtotal
        self.assertEqual((sale.order_line - line).mapped("price_subtotal"), [0, 0, 0])
        # Pack price is equal to the sum of component prices
        self.assertEqual(line.price_subtotal, 2662.5)
        self.assertEqual(self._get_component_prices_sum(self.product_pdt), 2662.5)

    def test_create_non_detailed_price_order_line(self):
        """Test with the same premise that in sale_product_pack but in a frontend
        tour"""
        self.start_tour("/shop", "create_non_detailed_price_order_line", login="portal")
        sale = self.env["sale.order"].search([], limit=1)
        line = sale.order_line.filtered(lambda x: x.product_id == self.product_pnd)
        # After create, there will be only one line, because product_type is
        # not a detailed one
        self.assertEqual(len(line), 1)
        # Pack price is equal to the sum of component prices
        self.assertEqual(line.price_subtotal, 2662.5)
        self.assertEqual(self._get_component_prices_sum(self.product_pnd), 2662.5)
