import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";

class ProductAttributeOptionPlugin extends Plugin {
    static id = "productAttributeOption";
    resources = {
        builder_options: {
            template: "website_sale.ProductAttributeOption",
            selector: "#product_detail .o_wsale_product_attribute",
            editableOnly: false,
            reloadTarget: true,
        },
        builder_actions: {
            productAttributeDisplay: new ProductAttributeDisplayAction(this),
        },
    };

    getProductAttributeDisplay(el) {
        return el.closest("[data-attribute_display_type]").dataset.attribute_display_type;
    }
}

class ProductAttributeDisplayAction extends BuilderAction {
    setup() {
        this.reload = false
    }
    isApplied({ editingElement: el, value }) {
        return value === this.plugin.getProductAttributeDisplay(el);
    }
    getValue({ editingElement: el }) {
        return this.plugin.getProductAttributeDisplay(el);
    }
    async apply({ editingElement: el, value }) {
        const attributeID = parseInt(
            el.closest("[data-attribute_id]").dataset.attribute_id
        );
        await rpc("/shop/config/attribute", {
            attribute_id: attributeID,
            display_type: value,
        });
    }
}

registry
    .category("website-plugins")
    .add(ProductAttributeOptionPlugin.id, ProductAttributeOptionPlugin);
