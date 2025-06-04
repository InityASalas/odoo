import { ProductsListPageOption } from "@website_sale/website_builder/products_list_page_option";
import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";

class ProductsListPageOptionPlugin extends Plugin {
    static id = "productsListPageOptionPlugin";
    resources = {
        builder_options: [
            {
                OptionComponent: ProductsListPageOption,
                selector: "main:has(.o_wsale_products_page)",
                applyTo: "#o_wsale_container",
                editableOnly: false,
                title: _t("Products Page"),
                groups: ["website.group_website_designer"],
            },
        ],
        builder_actions: {
            setPpg: new SetPpgAction(this),
            setPpr: new SetPprAction(this),
            setGap: new SetGapAction(this),
            setDefaultSort: new SetDefaultSortAction(this),
        }
    };
}

class SetPpgAction extends BuilderAction {
    setup() {
        this.reload = false;
    }
    getValue({ editingElement }) {
        return parseInt(editingElement.dataset.ppg);
    }
    apply({ value }) {
        const PPG_LIMIT = 10000;
        let ppg = parseInt(value);
        if (!ppg || ppg < 1) {
            return false;
        }
        ppg = Math.min(ppg, PPG_LIMIT);
        return rpc("/shop/config/website", { shop_ppg: ppg });
    }
}
class SetPprAction extends BuilderAction {
    setup() {
        this.reload = false;
    }
    isApplied({ editingElement, value }) {
        return parseInt(editingElement.dataset.ppr) === value;
    }
    apply({ value }) {
        const ppr = parseInt(value);
        return rpc("/shop/config/website", { shop_ppr: ppr });
    }
}
class SetGapAction extends BuilderAction {
    setup() {
        this.reload = false;
    }
    apply({ value }) {
        return rpc("/shop/config/website", { shop_gap: value });
    }
}
class SetDefaultSortAction extends BuilderAction {
    setup() {
        this.reload = false;
    }
    isApplied({ editingElement, value }) {
        editingElement.dataset.defaultSort === value;
    }
    apply({ value }) {
        return rpc("/shop/config/website", { shop_default_sort: value });
    }
}

registry
    .category("website-plugins")
    .add(ProductsListPageOptionPlugin.id, ProductsListPageOptionPlugin);
