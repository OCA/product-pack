/** @odoo-module **/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {patch} from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    removeOrderline(line) {
        line.removePackLine();
        return super.removeOrderline(...arguments);
    },
});
