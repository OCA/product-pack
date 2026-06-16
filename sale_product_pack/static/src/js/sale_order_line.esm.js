/** @odoo-module **/
/* Copyright 2026 ACSONE SA/NV */
/* Copyright 2026 Atrium res Informatica */
import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {StaticList} from "@web/model/relational_model/static_list";

patch(StaticList.prototype, {
    _getRecordIdentifier(record) {
        return record?.resId || record?.id || null;
    },

    _isSaleOrderLine(record) {
        return Boolean(record && record.resModel === "sale.order.line");
    },

    _isPackChildRecord(record) {
        return (
            this._isSaleOrderLine(record) &&
            Boolean(record.data && record.data.pack_parent_line_id)
        );
    },

    _isPackParentRecord(record) {
        return (
            this._isSaleOrderLine(record) &&
            !(record.data && record.data.pack_parent_line_id)
        );
    },

    _getParentId(record) {
        return record?.data?.pack_parent_line_id?.[0] || null;
    },

    _getPackChildRecords(parentRecord, records) {
        const sourceRecords = Array.isArray(records) ? records : [];
        const parentId = this._getRecordIdentifier(parentRecord);
        if (!parentId) {
            return [];
        }
        return sourceRecords.filter(
            (record) =>
                this._isPackChildRecord(record) &&
                this._getParentId(record) === parentId
        );
    },

    _expandRecordsToDelete(records) {
        // When a pack parent is deleted from the list, include its current child
        // lines in the same delete batch so backend constraints stay consistent.
        const selectedRecords = Array.isArray(records) ? records : [];
        const currentRecords = Array.isArray(this.records) ? this.records : [];
        const result = [...selectedRecords];
        const seen = new Set(
            selectedRecords.map((record) => this._getRecordIdentifier(record))
        );

        for (const record of selectedRecords) {
            if (!this._isPackParentRecord(record)) {
                continue;
            }
            for (const childRecord of this._getPackChildRecords(
                record,
                currentRecords
            )) {
                const childId = this._getRecordIdentifier(childRecord);
                if (!seen.has(childId)) {
                    result.push(childRecord);
                    seen.add(childId);
                }
            }
        }
        return result;
    },

    _isChildDeletedWithoutParent(record, selectedParentIds) {
        return (
            this._canBeDeleted(record) &&
            !selectedParentIds.has(this._getParentId(record))
        );
    },

    _canBeDeleted(record) {
        // Protected children of non-modifiable packs cannot be removed directly.
        return (
            this._isPackChildRecord(record) &&
            !(record.data && record.data.pack_modifiable)
        );
    },

    _alertNotUnlinkable() {
        const body = _t(
            "Cannot delete this line because it is part of a pack. Delete the pack itself."
        );

        this.model.env.services.dialog.add(AlertDialog, {
            title: _t("Deletion not allowed"),
            body: body,
        });
    },

    async delete(record) {
        return this.deleteRecords([record]);
    },

    async _superDeleteRecords(records) {
        // Compatibility fallback: some StaticList contexts expose only `delete`.
        if (super.deleteRecords) {
            return super.deleteRecords(records);
        }
        for (const record of records) {
            await super.delete(record);
        }
    },

    async deleteRecords(records) {
        if (!Array.isArray(records)) {
            if (super.deleteRecords) {
                return super.deleteRecords(...arguments);
            }
            return super.delete(records);
        }
        const recordsToDelete = this._expandRecordsToDelete(records);
        const selectedParentIds = new Set(
            recordsToDelete
                .filter((record) => !this._isPackChildRecord(record))
                .map((record) => this._getRecordIdentifier(record))
        );
        const hasProtectedChild = recordsToDelete.some((record) =>
            this._isChildDeletedWithoutParent(record, selectedParentIds)
        );
        if (hasProtectedChild) {
            // Block only when a protected child is targeted without its parent.
            this._alertNotUnlinkable();
            return;
        }
        return this._superDeleteRecords(recordsToDelete);
    },
});
