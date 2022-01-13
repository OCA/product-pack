odoo.define("pos_product_pack.OrderlineDetails", function (require) {
    "use strict";

    var OrderlineDetails = require("point_of_sale.OrderlineDetails");
    const {useListener} = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");

    const PackOrderLineDetails = (OrderlineDetails) =>
        class extends OrderlineDetails {
            constructor() {
                super(...arguments);
                // UseListener('click', this.onClick);
            }
            async onSelect() {
                alert(this);
            }
        };
    Registries.Component.extend(OrderlineDetails, PackOrderLineDetails);

    return OrderlineDetails;
});
