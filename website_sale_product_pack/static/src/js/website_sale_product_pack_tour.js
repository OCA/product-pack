/* Copyright 2021 Tecnativa - David Vidal
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */

odoo.define(
    "website_sale_product_pack.tour_create_components_price_order_line",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        var steps = [
            {
                trigger:
                    "a:contains('Pack CPU (Detailed - Displayed Components Price)')",
            },
            {
                trigger: "a:contains('Add to Cart')",
            },
            {
                trigger: "a:contains('Process Checkout')",
            },
            {
                trigger: "a[href='/shop']",
            },
        ];
        tour.register(
            "create_components_price_order_line",
            {
                url: "/shop",
                test: true,
            },
            steps
        );
    }
);

odoo.define(
    "website_sale_product_pack.tour_create_ignored_price_order_line",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        var steps = [
            {
                trigger: "a:contains('Pack CPU (Detailed - Ignored Components Price)')",
            },
            {
                trigger: "a:contains('Add to Cart')",
            },
            {
                trigger: "a:contains('Process Checkout')",
            },
            {
                trigger: "a[href='/shop']",
            },
        ];
        tour.register(
            "create_ignored_price_order_line",
            {
                url: "/shop",
                test: true,
            },
            steps
        );
    }
);

odoo.define(
    "website_sale_product_pack.tour_create_totalized_price_order_line",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        var steps = [
            {
                trigger:
                    "a:contains('Pack CPU (Detailed - Totalized Components Price)')",
            },
            {
                trigger: "a:contains('Add to Cart')",
            },
            {
                trigger: "a:contains('Process Checkout')",
            },
            {
                trigger: "a[href='/shop']",
            },
        ];
        tour.register(
            "create_totalized_price_order_line",
            {
                url: "/shop",
                test: true,
            },
            steps
        );
    }
);

odoo.define(
    "website_sale_product_pack.tour_create_non_detailed_price_order_line",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        var steps = [
            {
                trigger: "a:contains('Non Detailed - Totalized Components Price')",
            },
            {
                trigger: "a:contains('Add to Cart')",
            },
            {
                trigger: "a:contains('Process Checkout')",
            },
            {
                trigger: "a[href='/shop']",
            },
        ];
        tour.register(
            "create_non_detailed_price_order_line",
            {
                url: "/shop",
                test: true,
            },
            steps
        );
    }
);

odoo.define("website_sale_product_pack.tour_update_pack_qty", function (require) {
    "use strict";

    var tour = require("web_tour.tour");

    var steps = [
        {
            trigger: "a:contains('Pack CPU (Detailed - Displayed Components Price)')",
        },
        {
            trigger: "a:contains('Add to Cart')",
        },
        {
            trigger: "a:contains('Process Checkout')",
        },
        {
            trigger: "a[href='/shop']",
        },
    ];
    tour.register(
        "update_pack_qty",
        {
            url: "/shop",
            test: true,
        },
        steps
    );
});
