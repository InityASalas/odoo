import { normalizeCSSColor } from "@web/core/utils/colors";

let editableWindow = window;

/**
 * @param {string} key
 * @param {CSSStyleDeclaration} [htmlStyle] if not provided, it is computed
 * @returns {string}
 */
export function getCSSVariableValue(key, htmlStyle) {
    if (htmlStyle === undefined) {
        htmlStyle = editableWindow.getComputedStyle(editableWindow.document.documentElement);
    }
    // Get trimmed value from the HTML element
    let value = htmlStyle.getPropertyValue(`--${key}`).trim();
    // If it is a color value, it needs to be normalized
    value = normalizeCSSColor(value);
    // Normally scss-string values are "printed" single-quoted. That way no
    // magic conversation is needed when customizing a variable: either save it
    // quoted for strings or non quoted for colors, numbers, etc. However,
    // Chrome has the annoying behavior of changing the single-quotes to
    // double-quotes when reading them through getPropertyValue...
    return value.replace(/"/g, "'");
}