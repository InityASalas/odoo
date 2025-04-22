import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class ShowIconField extends Component {
    static template = "hr_skills.ShowIconField";
    static props = {
        ...standardFieldProps,
        icon: { type: String, optional: true },
        title: { type: String, optional: true },
        color: { type: String, optional: true },
    };
    static defaultProps = {
        icon: "fa-warning",
        color: "text-warning",
    };

}

export const showIconField = {
    component: ShowIconField,
    displayName: _t("Show Boolean Icon"),
    supportedOptions: [
        {
            label: _t("Icon"),
            name: "icon",
            type: "string",
        },
        {
            label: _t("Color"),
            name: "color",
            type: "string",
        },
    ],
    supportedTypes: ["boolean"],
    extractProps: ({ options, string }) => ({
        icon: options.icon,
        title: string,
    }),
};

registry.category("fields").add("show_icon", showIconField);