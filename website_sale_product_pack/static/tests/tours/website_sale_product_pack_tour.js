/** @odoo-module **/
/* Copyright 2021 Tecnativa - David Vidal
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import {registry} from "@web/core/registry";
import tourUtils from "@website_sale/js/tours/tour_utils";

registry.category("web_tour.tours").add("create_components_price_order_line", {
    test: true,
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Pack CPU (Detailed - Displayed Components Price)"),
        {
            content: "select Pack CPU (Detailed - Displayed Components Price)",
            trigger:
                '.oe_product_cart:first a:contains("Pack CPU (Detailed - Displayed Components Price)")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart(),
    ],
});

registry.category("web_tour.tours").add("create_ignored_price_order_line", {
    test: true,
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Pack CPU (Detailed - Ignored Components Price)"),
        {
            content: "select Pack CPU (Detailed - Ignored Components Price)",
            trigger:
                '.oe_product_cart:first a:contains("Pack CPU (Detailed - Ignored Components Price)")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart(),
    ],
});

registry.category("web_tour.tours").add("create_totalized_price_order_line", {
    test: true,
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Pack CPU (Detailed - Totalized Components Price)"),
        {
            content: "select Pack CPU (Detailed - Totalized Components Price)",
            trigger:
                '.oe_product_cart:first a:contains("Pack CPU (Detailed - Totalized Components Price)")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart(),
    ],
});

registry.category("web_tour.tours").add("create_non_detailed_price_order_line", {
    test: true,
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Non Detailed - Totalized Components Price"),
        {
            content: "select Non Detailed - Totalized Components Price",
            trigger:
                '.oe_product_cart:first a:contains("Non Detailed - Totalized Components Price")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart(),
    ],
});

registry.category("web_tour.tours").add("update_pack_qty", {
    test: true,
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Pack CPU (Detailed - Displayed Components Price)"),
        {
            content: "select Pack CPU (Detailed - Displayed Components Price)",
            trigger:
                '.oe_product_cart:first a:contains("Pack CPU (Detailed - Displayed Components Price)")',
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
        },
        tourUtils.goToCart({quantity: 1}),
    ],
});
