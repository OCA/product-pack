/** @odoo-module **/

import {SaleOrderLineListRenderer} from "@sale/js/sale_order_line_field/sale_order_line_field";
import {patch} from "@web/core/utils/patch";

patch(SaleOrderLineListRenderer.prototype, {
    getRowClass(record) {
        const classNames = super.getRowClass(record);
        return `${classNames} ${record.data.pack_is_visual_header ? "o_is_line_section o_is_line_section_no_indent" : ""}`;
    },
});
