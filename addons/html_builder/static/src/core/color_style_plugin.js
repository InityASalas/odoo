import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { applyNeededCss } from "@html_builder/utils/utils_css";
import { withSequence } from "@html_editor/utils/resource";
import { BuilderAction } from "./core_builder_action_plugin";

class ColorStylePlugin extends Plugin {
    static id = "colorStyle";
    static dependencies = ["color"];
    resources = {
        builder_style_actions: {
            "background-color": new StyleColorBaseAction("background", "bg", this),
            color: new StyleColorBaseAction("color", "text", this),
        },
        apply_style: withSequence(5, (element, cssProp, color) => {
            applyNeededCss(element, cssProp, color);
            return true;
        }),
    };
}

class StyleColorBaseAction extends BuilderAction {
    /**
     * @param {string} property - CSS property name (e.g. 'color', 'backgroundColor')
     * @param {string} classPrefix - Bootstrap class prefix (e.g. 'text-', 'bg-')
     * @param {Object} plugin - injected plugin
     */
    constructor(property, classPrefix, plugin) {
        super(plugin);
        this.property = property;
        this.classPrefix = classPrefix;
    }

    /**
     * Retrieves the computed color or background color of the given element.
     *
     * @param {Object} args
     *   - `editingElement` {HTMLElement}: the element from which to get the color
     * @returns {string} the current color or background color value
     */
    getValue({ editingElement }) {
        return this.dependencies.color.getElementColors(editingElement)[this.property];
    }

    /**
     * Applies a Bootstrap color class to the given element. If the value is a
     * CSS variable (e.g., `var(--bs-primary)`), it is converted to a class name.
     *
     * @param {Object} args
     *   - `editingElement` {HTMLElement}: the element to apply the color to
     *   - `params.mainParam` {string}: the color value to apply
     */
    apply({ editingElement, params = {} }) {
        let value = params.mainParam;
        const match = value.match(/var\(--([a-zA-Z0-9-_]+)\)/);
        if (match) {
            value = `${this.classPrefix}${match[1]}`;
        }
        this.dependencies.color.colorElement(editingElement, value, this.property);
    }
}

registry.category("website-plugins").add(ColorStylePlugin.id, ColorStylePlugin);
