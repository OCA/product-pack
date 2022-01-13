odoo.define("pos_product_pack.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.load_fields("product.template", ["pack_ok"]);
    models.load_fields("product.product", [
        "pack_ok",
        "pack_line_ids",
        "pack_type",
        "pack_component_price",
    ]);
    // Load product.pack.line that parent is avaiable in pos
    models.load_models([
        {
            model: "product.pack.line",
            fields: ["parent_product_id", "quantity", "product_id"],
            // Condition: function (self) { return self.product_by_id; },
            domain: function () {
                return [["parent_product_id.available_in_pos", "=", true]];
            },
            loaded: function (self, product_pack_line_ids) {
                self.product_pack_line_by_id = {};
                _.map(product_pack_line_ids, function (product_pack_line) {
                    self.product_pack_line_by_id[
                        product_pack_line.id
                    ] = product_pack_line;
                });
            },
        },
    ]);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        add_product_pack: function (line) {
            // Get parent children and for each of them, add the product
            var self = this;
            var pack_lines = line.get_pack_lines();
            _.forEach(pack_lines, function (pack_line) {
                var product = self.pos.db.get_product_by_id(pack_line.product_id[0]);
                if (product) {
                    self.add_product(product, {
                        pack_parent_line_id: line,
                        pack_line_id: pack_line,
                    });
                }
            });
        },

        // @Override
        add_product(product, options) {
            _super_order.add_product.apply(this, arguments);
            var line = this.get_selected_orderline();
            // Added product is a pack - We add products contained in that
            // pack.
            if (product.pack_ok) {
                this.add_product_pack(line);
            }
            // Added product is one contained in a parent pack.
            // We add the line in children variable in parent pack.
            if ("pack_parent_line_id" in options) {
                if (line.pack_parent_line_id === null) {
                    line.pack_parent_line_id = options.pack_parent_line_id;
                }
                if (
                    !options.pack_parent_line_id.pack_child_line_ids.some(
                        (child) => child === line.id
                    )
                ) {
                    var parent_line = this.get_orderline(
                        options.pack_parent_line_id.id
                    );
                    parent_line.pack_child_line_ids.push(line.id);
                    // Force a save as pack child lines are just ids
                    parent_line.order.save_to_db();
                }
            }
            if ("pack_line_id" in options) {
                line.pack_line_id = options.pack_line_id;
                line.order.save_to_db();
            }
        },
        // @Override
        remove_orderline: function (line) {
            line.remove_pack_line();
            _super_order.remove_orderline.apply(this, arguments);
        },
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize() {
            // Define pack parent and children values
            this.pack_parent_line_id = null;
            this.pack_line_id = null;
            this.pack_child_line_ids = [];
            _super_order_line.initialize.apply(this, arguments);
        },
        get_pack_lines: function () {
            // Return pack lines from pack product
            var pack_line_ids = this.get_product().pack_line_ids;
            var lines = [];
            for (var i = 0; i < pack_line_ids.length; i++) {
                if (this.pos.product_pack_line_by_id[pack_line_ids[i]]) {
                    lines.push(this.pos.product_pack_line_by_id[pack_line_ids[i]]);
                }
            }
            return lines;
        },
        remove_pack_line: function () {
            var self = this;
            // Check if line is a pack one and has children
            if (this.product.pack_ok) {
                // The line to remove is a product pack
                // So, we remove the concerning children lines
                if (this.pack_child_line_ids) {
                    this.pack_child_line_ids.forEach(function (child_line_id) {
                        var child_line = self.order.get_orderline(child_line_id);
                        if (child_line) {
                            self.order.remove_orderline(child_line);
                        }
                    });
                }
            }
        },
        set_pack_lines_quantity: function (quantity) {
            var self = this;
            if (this.product.pack_ok && this.pack_child_line_ids.length) {
                this.pack_child_line_ids.forEach(function (child_line_id) {
                    var child_line = self.order.get_orderline(child_line_id);
                    if (child_line) {
                        child_line.set_quantity(quantity);
                    }
                });
            }
        },
        merge: function () {
            if (this.pack_line_id) {
                // This would avoid to call set_quantity twice
                return;
            }
            return _super_order_line.merge.apply(this, arguments);
        },
        // @Override
        set_quantity: function (quantity) {
            _super_order_line.set_quantity.apply(this, arguments);
            this.set_pack_lines_quantity(quantity);
        },
        get_full_product_name: function () {
            var name = _super_order_line.get_full_product_name.apply(this, arguments);
            if (this.pack_line_id) {
                name = "> " + name;
            }
            return name;
        },
        // @Override
        init_from_JSON: function (json) {
            _super_order_line.init_from_JSON.apply(this, arguments);
            if (json.pack_parent_line_id) {
                this.pack_parent_line_id = this.order_id.get_orderline(
                    json.pack_parent_line_id
                );
            }
            if (json.pack_child_line_ids) {
                var pack_child_line_ids = json.pack_child_line_ids;
                this.pack_child_line_ids = [];
                for (var i = 0; i < pack_child_line_ids.length; i++) {
                    var pack_child = pack_child_line_ids[i][2];
                    this.pack_child_line_ids.push(pack_child);
                }
            }
        },
        // @Override
        export_as_JSON: function () {
            const json = _super_order_line.export_as_JSON.apply(this, arguments);
            var pack_child_ids = [];
            // Export children
            this.pack_child_line_ids.forEach(function (child) {
                return pack_child_ids.push([4, 0, child]);
            });
            // Export parent
            if (this.pack_parent_line_id) {
                json.pack_parent_line_id = this.pack_parent_line_id.id;
            }
            if (this.pack_line_id) {
                json.pack_line_id = this.pack_line_id.id;
            }
            json.pack_child_line_ids = pack_child_ids;
            return json;
        },
    });
});
