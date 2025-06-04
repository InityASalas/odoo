import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";
import { before, SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

class CountdownOptionPlugin extends Plugin {
    static id = "CountdownOption";
    resources = {
        builder_options: [
            withSequence(before(SNIPPET_SPECIFIC_END), {
                template: "website.CountdownOption",
                selector: ".s_countdown",
                cleanForSave: this.cleanForSave.bind(this),
            }),
        ],
        so_content_addition_selector: [".s_countdown"],
        builder_actions: {
            // TODO AGAU: update after merging generalized restart interactions
            //  remove this and xml BuilderContext
            reloadCountdown: new ReloadCountdownAction(this),
            setEndAction: new SetEndActionAction(this),
            previewEndMessage: new PreviewEndMessageAction(this),
            setLayout: new SetLayoutAction(this),
        },
    };

    /**
     * Used to preserve modified end messages through end action changes. This
     * allows the user to test options without losing their progress while in
     * between saves.
     *
     * @type {WeakMap<Element, Element>}
     */
    editingElEndMessages = new WeakMap();

    cleanForSave(editingEl) {
        editingEl.classList.remove("s_countdown_enable_preview");
    }

    setEndAction({ editingElement, value }) {
        editingElement.dataset.endAction = value;
        const endMessageEl = editingElement.querySelector(".s_countdown_end_message");

        // Only hide countdown in one case
        editingElement.classList.toggle("hide-countdown", value === "message_no_countdown");

        // Only have redirect url attribute in one case
        if (value === "redirect") {
            editingElement.dataset.redirectUrl = "";
        } else {
            delete editingElement.dataset.redirectUrl;
        }

        if (value === "message" || value === "message_no_countdown") {
            if (!endMessageEl) {
                const existingEndMessage = this.editingElEndMessages.get(editingElement);
                editingElement.appendChild(
                    existingEndMessage || renderToElement("website.s_countdown.end_message")
                );
            }
        } else {
            endMessageEl?.remove();
            this.editingElEndMessages.set(editingElement, endMessageEl);
            // Reset end message preview to avoid countdown staying hidden
            this.toggleEndMessagePreview(editingElement, false);
        }
    }

    isEndActionApplied({ editingElement, value }) {
        return editingElement.dataset.endAction === value;
    }

    setLayout({ editingElement, value }) {
        switch (value) {
            case "circle":
                editingElement.dataset.progressBarStyle = "disappear";
                editingElement.dataset.progressBarWeight = "thin";
                editingElement.dataset.layoutBackground = "none";
                break;
            case "boxes":
                editingElement.dataset.progressBarStyle = "none";
                editingElement.dataset.layoutBackground = "plain";
                break;
            case "clean":
                editingElement.dataset.progressBarStyle = "none";
                editingElement.dataset.layoutBackground = "none";
                break;
            case "text":
                editingElement.dataset.progressBarStyle = "none";
                editingElement.dataset.layoutBackground = "none";
                break;
        }
        editingElement.dataset.layout = value;
    }

    isLayoutApplied({ editingElement, value }) {
        return editingElement.dataset.layout === value;
    }

    isEndMessagePreviewed({ editingElement }) {
        return !!editingElement?.classList.contains("s_countdown_enable_preview");
    }

    toggleEndMessagePreview(editingElement, doShow) {
        editingElement?.classList.toggle("s_countdown_enable_preview", doShow === true);
    }
}

// TODO AGAU: update after merging generalized restart interactions
//  remove this and xml BuilderContext
class ReloadCountdownAction extends BuilderAction {
    apply({ editingElement }) {
        return this.plugin.dispatchTo("update_interactions", editingElement);
    }
}

class SetEndActionAction extends BuilderAction {
    apply(context) {
        return this.plugin.setEndAction(context);
    }
    isApplied(context) {
        return this.plugin.isEndActionApplied(context);
    }
}

class PreviewEndMessageAction extends BuilderAction {
    apply({ editingElement }) {
        return this.plugin.toggleEndMessagePreview(editingElement, true);
    }
    clean({ editingElement }) {
        return this.plugin.toggleEndMessagePreview(editingElement, false);
    }
    isApplied(context) {
        return this.plugin.isEndMessagePreviewed(context);
    }
}

class SetLayoutAction extends BuilderAction {
    apply(context) {
        return this.plugin.setLayout(context);
    }
    isApplied(context) {
        return this.plugin.isLayoutApplied(context);
    }
}
registry.category("website-plugins").add(CountdownOptionPlugin.id, CountdownOptionPlugin);
