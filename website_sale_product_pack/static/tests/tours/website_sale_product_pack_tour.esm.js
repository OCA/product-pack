/* Copyright 2021 Tecnativa - David Vidal
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

import * as tourUtils from "@website_sale/js/tours/tour_utils";
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("create_components_price_order_line", {
    url: "/shop",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Pack CPU (Detailed - Displayed Components Price)",
            expectUnloadPage: true,
        }),
        tourUtils.goToCart({quantity: 1}),
    ],
});

registry.category("web_tour.tours").add("create_ignored_price_order_line", {
    url: "/shop",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Pack CPU (Detailed - Ignored Components Price)",
            expectUnloadPage: true,
        }),
        tourUtils.goToCart({quantity: 1}),
    ],
});

registry.category("web_tour.tours").add("create_totalized_price_order_line", {
    url: "/shop",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Pack CPU (Detailed - Totalized Components Price)",
            expectUnloadPage: true,
        }),
        tourUtils.goToCart({quantity: 1}),
    ],
});

registry.category("web_tour.tours").add("create_non_detailed_price_order_line", {
    url: "/shop",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Non Detailed - Totalized Components Price",
            expectUnloadPage: true,
        }),
        tourUtils.goToCart({quantity: 1}),
    ],
});

registry.category("web_tour.tours").add("update_pack_qty", {
    url: "/shop",
    steps: () => [
        ...tourUtils.addToCart({
            productName: "Pack CPU (Detailed - Displayed Components Price)",
            expectUnloadPage: true,
        }),
        tourUtils.goToCart({quantity: 1}),
    ],
});
