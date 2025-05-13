import { Component } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { toolbarButtonProps } from "@html_editor/main/toolbar/toolbar";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { useDropdownAutoClose } from "@html_editor/dropdown_autoclose_hook";

export class ImagePadding extends Component {
    static components = { Dropdown, DropdownItem };
    static props = {
        ...toolbarButtonProps,
        onSelected: Function,
    };
    static template = "html_editor.ImagePadding";

    setup() {
        this.paddings = { None: 0, Small: 1, Medium: 2, Large: 3, XL: 5 };
        this.dropdown = useDropdownState();
        useDropdownAutoClose(this.props.overlayState, this.dropdown);
    }

    onSelected(padding) {
        this.props.onSelected({ size: this.paddings[padding] });
    }
}
