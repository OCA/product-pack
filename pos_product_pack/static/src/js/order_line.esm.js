/** @odoo-module **/

import {PosOrderline} from "@point_of_sale/app/models/pos_order_line";
import {patch} from "@web/core/utils/patch";

function isPackChild(line) {
    return Boolean(line.pack_line_id || line.pack_parent_line_id);
}

patch(PosOrderline.prototype, {
    getPackLines() {
        return this.getProduct().pack_line_ids || [];
    },

    getPackLineCanBeMergedWith(packLine) {
        return (
            this.order_id.lines.find(
                (line) =>
                    line.pack_parent_line_id?.id === this.id &&
                    line.pack_line_id?.id === packLine.id
            ) || null
        );
    },

    removePackLine() {
        if (this.getProduct().pack_ok) {
            for (const childLine of [...this.pack_child_line_ids]) {
                this.order_id.removeOrderline(childLine);
            }
        }

        if (this.pack_parent_line_id) {
            this.pack_parent_line_id.pack_child_line_ids = [["unlink", this]];
        }
    },

    setPackLinesQuantity(quantity) {
        if (this.getProduct().pack_ok) {
            for (const childLine of this.pack_child_line_ids) {
                childLine.setQuantity(
                    quantity * (childLine.pack_line_id?.quantity || 1)
                );
            }
        }
    },

    canBeMergedWith(orderline) {
        if (isPackChild(this) || isPackChild(orderline)) {
            return (
                this.pack_parent_line_id &&
                orderline.pack_parent_line_id &&
                this.pack_parent_line_id.id === orderline.pack_parent_line_id.id &&
                this.getProduct().id === orderline.getProduct().id &&
                this.pack_line_id?.id === orderline.pack_line_id?.id
            );
        }

        return super.canBeMergedWith(...arguments);
    },

    merge() {
        if (this.pack_line_id) {
            return;
        }

        return super.merge(...arguments);
    },

    setQuantity(quantity) {
        const result = super.setQuantity(...arguments);
        this.setPackLinesQuantity(quantity);
        return result;
    },

    setFullProductName() {
        super.setFullProductName(...arguments);

        if (this.pack_line_id && !this.full_product_name.startsWith("> ")) {
            this.full_product_name = `> ${this.full_product_name}`;
        }
    },

    getFullProductName() {
        const name = super.getFullProductName(...arguments);

        if (this.pack_line_id && !name.startsWith("> ")) {
            return `> ${name}`;
        }

        return name;
    },

    get orderDisplayProductName() {
        const displayName = super.orderDisplayProductName;

        if (this.pack_line_id && !displayName.name.startsWith("> ")) {
            return {
                ...displayName,
                name: `> ${displayName.name}`,
            };
        }

        return displayName;
    },
    getDisplayClasses() {
        return {
            ...super.getDisplayClasses(...arguments),
            o_pack_child_line: Boolean(this.pack_parent_line_id),
            o_pack_parent_line: Boolean(this.pack_child_line_ids?.length),
        };
    },
});
