import {
    getCurrentShadow,
    getDefaultShadow,
    SetShadowAction,
    SetShadowModeAction,
    shadowToString,
} from "@html_builder/plugins/shadow_option_plugin";
import {
    SNIPPET_SPECIFIC_END,
    SNIPPET_SPECIFIC_NEXT,
    splitBetween,
} from "@html_builder/utils/option_sequence";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { HeaderBorderOption } from "./header_border_option";
import { HeaderElementOption } from "./header_element_option";
import { StyleAction } from "@html_builder/core/core_builder_action_plugin";

const [
    HEADER_TEMPLATE,
    HEADER_TEMPLATE_SECONDARY_OPTIONS,
    HEADER_BORDER,
    HEADER_SCROLL_EFFECT,
    HEADER_ELEMENT,
    HEADER_END,
    ...__ERROR_CHECK__
] = splitBetween(SNIPPET_SPECIFIC_NEXT, SNIPPET_SPECIFIC_END, 6);
if (__ERROR_CHECK__.length > 0) {
    console.error("Wrong count in header option split");
}

export {
    HEADER_TEMPLATE,
    HEADER_TEMPLATE_SECONDARY_OPTIONS,
    HEADER_BORDER,
    HEADER_SCROLL_EFFECT,
    HEADER_ELEMENT,
    HEADER_END,
};

class HeaderOptionPlugin extends Plugin {
    static id = "headerOption";
    static dependencies = ["customizeWebsite", "shadowOption"];

    resources = {
        builder_options: [
            withSequence(HEADER_TEMPLATE, {
                editableOnly: false,
                template: "website.headerTemplateOption",
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            withSequence(HEADER_TEMPLATE_SECONDARY_OPTIONS, {
                editableOnly: false,
                template: "website.headerContentWidthOption",
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            withSequence(HEADER_TEMPLATE_SECONDARY_OPTIONS, {
                editableOnly: false,
                template: "website.headerSidebarWidthOption",
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            withSequence(HEADER_TEMPLATE_SECONDARY_OPTIONS, {
                editableOnly: false,
                template: "website.headerBackgroundOption",
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            // TODO Header box (border & shadow) ?
            withSequence(HEADER_SCROLL_EFFECT, {
                editableOnly: false,
                template: "website.headerScrollEffectOption",
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            withSequence(HEADER_ELEMENT, {
                editableOnly: false,
                OptionComponent: HeaderElementOption,
                selector: "#wrapwrap > header",
                groups: ["website.group_website_designer"],
            }),
            withSequence(HEADER_BORDER, {
                editableOnly: false,
                OptionComponent: HeaderBorderOption,
                selector: "#wrapwrap > header",
                applyTo: ".navbar:not(.d-none)",
                groups: ["website.group_website_designer"],
            }),
        ],
        builder_actions: {
            styleActionHeader: new StyleActionHeaderAction(this),
            setShadowModeHeader: new SetShadowModeHeaderAction(this),
            setShadowHeader: new SetShadowHeaderAction(this),
        },
    };
    setup() {
        this.withCustomHistory = this.dependencies.customizeWebsite.withCustomHistory;
    }
}

class StyleActionHeaderAction extends StyleAction {
    setup() {
        this.customHistory = this.plugin.withCustomHistory;
    }
    getValue(...args) {
        const { params } = args[0];
        const value = super.getValue(...args);
        if (params.mainParam === "border-width") {
            return value.replace(/(^|\s)0px/gi, "").trim() || value;
        }
        return value;
    }
    async apply({ params, value }) {
        const styleName = params.mainParam;

        if (styleName === "border-color") {
            return this.dependencies.customizeWebsite.customizeWebsiteColors({
                "menu-border-color": value,
            });
        }
        return this.dependencies.customizeWebsite.customizeWebsiteVariables({
            [`menu-${styleName}`]: value,
        });
    }
}

class SetShadowModeHeaderAction extends SetShadowModeAction {
    setup() {
        //this.preview = false;
        this.customHistory = this.plugin.withCustomHistory;
    }
    async apply({ value: shadowMode }) {
        const defaultShadow = shadowMode === "none" ? "none" : getDefaultShadow(shadowMode);
        return this.dependencies.customizeWebsite.customizeWebsiteVariables({
            "menu-box-shadow": defaultShadow,
        });
    }
}

class SetShadowHeaderAction extends SetShadowAction {
    setup() {
        this.preview = false;
        this.customHistory = this.plugin.withCustomHistory;
    }
    async apply({ editingElement, params: { mainParam: attributeName }, value }) {
        const shadow = getCurrentShadow(editingElement);
        shadow[attributeName] = value;

        return this.dependencies.customizeWebsite.customizeWebsiteVariables({
            "menu-box-shadow": shadowToString(shadow),
        });
    }
}

registry.category("website-plugins").add(HeaderOptionPlugin.id, HeaderOptionPlugin);
