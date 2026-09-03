/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async addProductPack(line) {
        for (const packLine of line.getPackLines()) {
            const product = packLine.product_id;

            if (!product) {
                continue;
            }

            const toMergeLine = line.getPackLineCanBeMergedWith(packLine);

            if (toMergeLine) {
                toMergeLine.merge();
            } else {
                await this.addLineToOrder(
                    {
                        product_id: product,
                        product_tmpl_id: product.product_tmpl_id,
                        qty: line.getQuantity() * (packLine.quantity || 1),
                        pack_parent_line_id: line,
                        pack_line_id: packLine,
                    },
                    line.order_id,
                    {},
                    false
                );
            }
        }
    },

    async addLineToOrder() {
        const line = await super.addLineToOrder(...arguments);

        if (!line) {
            return line;
        }

        if (line.product_id.pack_ok) {
            await this.addProductPack(line);
        }

        return line;
    },
});
