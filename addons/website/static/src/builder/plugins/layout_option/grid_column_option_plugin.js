import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { GridColumnsOption } from "./grid_column_option";
import { withSequence } from "@html_editor/utils/resource";
import { GRID_COLUMNS } from "@website/builder/option_sequence";
import { StyleAction } from "@html_builder/core/core_builder_action_plugin";

export class GridColumnsOptionPlugin extends Plugin {
    static id = "GridColumnsOption";
    resources = {
        builder_options: [
            withSequence(GRID_COLUMNS, {
                OptionComponent: GridColumnsOption,
                selector: ".row:not(.s_col_no_resize) > div",
            }),
        ],
        builder_actions: {
            setGridColumnsPadding: new GridColumnsPaddingAction(this),
        },
        system_classes: ["o_we_padding_highlight"],
    };
}

registry.category("website-plugins").add(GridColumnsOptionPlugin.id, GridColumnsOptionPlugin);

class GridColumnsPaddingAction extends StyleAction {
    removePaddingPreview = ({ target: editingElement }) => {
        editingElement.classList.remove("o_we_padding_highlight");
        editingElement.removeEventListener("animationend", this.removePaddingPreview);
    };
    apply({ editingElement: el }) {
        this.removePaddingPreview({ target: el });
        super.apply(...arguments);
        el.classList.add("o_we_padding_highlight");
        el.addEventListener("animationend", this.removePaddingPreview);
    }
}
