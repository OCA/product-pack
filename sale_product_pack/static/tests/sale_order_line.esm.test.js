/** @odoo-module **/
/* Copyright 2026 Atrium res Informatica */

import {describe, expect, test} from "@odoo/hoot";

import {StaticList} from "@web/model/relational_model/static_list";

function makeContext(overrides = {}) {
    return Object.assign(Object.create(StaticList.prototype), overrides);
}

function makeSaleChildRecord({packModifiable = false} = {}) {
    return {
        resModel: "sale.order.line",
        data: {
            pack_parent_line_id: [99, "Pack"],
            pack_modifiable: packModifiable,
        },
    };
}

function makeSaleParentRecord({id = 99, packModifiable = false} = {}) {
    return {
        resModel: "sale.order.line",
        id,
        data: {
            pack_parent_line_id: false,
            pack_modifiable: packModifiable,
        },
    };
}

describe("sale_order_line.esm", () => {
    test("_canBeDeleted is true only for pack child", () => {
        const context = makeContext();

        expect(
            StaticList.prototype._canBeDeleted.call(
                context,
                makeSaleChildRecord({packModifiable: false})
            )
        ).toBe(true);
        expect(
            StaticList.prototype._canBeDeleted.call(
                context,
                makeSaleChildRecord({packModifiable: true})
            )
        ).toBe(false);
        expect(
            StaticList.prototype._canBeDeleted.call(context, {
                resModel: "sale.order.line",
                data: {pack_parent_line_id: false, pack_modifiable: false},
            })
        ).toBe(false);
    });

    test("delete on protected child opens warning dialog", async () => {
        let alertCalled = false;
        let superDeleteCount = 0;
        const context = makeContext({
            _alertNotUnlinkable: () => {
                alertCalled = true;
            },
            _superDeleteRecords: () => {
                superDeleteCount += 1;
            },
        });

        await StaticList.prototype.delete.call(
            context,
            makeSaleChildRecord({packModifiable: false})
        );

        expect(alertCalled).toBe(true);
        expect(superDeleteCount).toBe(0);
    });

    test("deleteRecords on protected children opens warning", async () => {
        let alertCalled = false;
        let superDeleteCount = 0;
        const context = makeContext({
            _alertNotUnlinkable: () => {
                alertCalled = true;
            },
            _superDeleteRecords: () => {
                superDeleteCount += 1;
            },
        });

        await StaticList.prototype.deleteRecords.call(context, [
            makeSaleChildRecord({packModifiable: false}),
            makeSaleChildRecord({packModifiable: false}),
        ]);

        expect(alertCalled).toBe(true);
        expect(superDeleteCount).toBe(0);
    });

    test("deleteRecords on parent expands to children", async () => {
        const scenarios = [{packModifiable: false}, {packModifiable: true}];

        for (const {packModifiable} of scenarios) {
            const parent = makeSaleParentRecord({packModifiable});
            const child = makeSaleChildRecord({packModifiable: false});
            let superDeleteRecordsArg = null;
            let alertCalled = false;
            const context = makeContext({
                records: [parent, child],
                _alertNotUnlinkable: () => {
                    alertCalled = true;
                },
                _superDeleteRecords: (records) => {
                    superDeleteRecordsArg = records;
                },
            });

            await StaticList.prototype.deleteRecords.call(context, [parent]);

            expect(Array.isArray(superDeleteRecordsArg)).toBe(true);
            expect(superDeleteRecordsArg).toHaveLength(2);
            expect(superDeleteRecordsArg.includes(parent)).toBe(true);
            expect(superDeleteRecordsArg.includes(child)).toBe(true);
            expect(alertCalled).toBe(false);
        }
    });
});
