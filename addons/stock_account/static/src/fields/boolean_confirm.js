import { _t } from "@web/core/l10n/translation";
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";

import { CheckBox } from "@web/core/checkbox/checkbox";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import {
    BooleanToggleField,
    booleanToggleField,
} from "@web/views/fields/boolean_toggle/boolean_toggle_field";

export class ConfirmCheckBox extends CheckBox {
    onClick(ev) {
        ev.preventDefault();

        if (ev.target.tagName !== "INPUT") {
            return;
        }
        this.props.onChange(ev.target.checked);
    }
}

export class BooleanToggleConfirm extends BooleanToggleField {
    static template = "stock_account.BooleanToggleConfirm";
    static components = { ConfirmCheckBox };

    setup() {
        super.setup();
        this.dialogService = useService('dialog');
    }

    async onChange(value) {
        const record = this.props.record.data;
        const updateAndSave = () => {
            this.props.record.update({ [this.props.name]: value }, { save: true });
        };

        const stockValuationLayersCount = await this.props.record.model.orm.call(
            "stock.valuation.layer",
            "search_count",
            [[['product_id', 'in', this.props.record.evalContext.product_variant_ids]]],
            { limit: 1 }
        );
        if (record.lot_valuated && !value && stockValuationLayersCount) {
            this.dialogService.add(ConfirmationDialog, {
                title: _t("Remove valuation by Lot/Serial Number"),
                body: _t("Removing this option means all specific valuations per lot or serial number will definitely be lost. Are you sure you want to proceed? "),
                confirmLabel: _t("Yes, set to the same value"),
                confirm: updateAndSave,
                cancel: () => {},
            });

        }
        else {
            updateAndSave();
        }
    }
}

export const booleanToggleConfirm = {
    ...booleanToggleField,
    component: BooleanToggleConfirm,
};

registry.category("fields").add("confirm_boolean", booleanToggleConfirm);
