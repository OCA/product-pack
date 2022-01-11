odoo.define('pos_product_pack.db', function (require) {
    "use strict";

    var PosDB = require('point_of_sale.PosDB');
    var utils = require('web.utils');
    /* The PosDB holds reference to data that is either
     * - static: does not change between pos reloads
     * - persistent : must stay between reloads ( orders )
     */

    var PosDB = PosDB.Class.extend({

    });
