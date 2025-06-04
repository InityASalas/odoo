import { ClassAction, StyleAction } from "@html_builder/core/core_builder_action_plugin";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";

class CardWidthOptionPlugin extends Plugin {
    static id = "cardWidthOption";
    resources = {
        builder_actions: {
            setCardWidth: new CardWidthAction(this),
            setCardAlignment: new CardAlignmentAction(this),
        },
    };
}

registry.category("website-plugins").add(CardWidthOptionPlugin.id, CardWidthOptionPlugin);

class CardAlignmentAction extends ClassAction {
    isApplied({ editingElement: el, params: { mainParam: classNames } }) {
        if (classNames === "me-auto") {
            return !["mx-auto", "ms-auto"].some((cls) => el.classList.contains(cls));
        }
        return super.isApplied(...arguments);
    }
}

class CardWidthAction extends StyleAction {
    getValue(...args) {
        const value = super.getValue(...args);
        return value.includes("%") ? value : "100%";
    }
}
