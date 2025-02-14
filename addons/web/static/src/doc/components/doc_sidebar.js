import { Component, useState, xml } from "@odoo/owl";
import { useModelStore } from "@web/doc/utils/doc_model_store";

export class DocSidebar extends Component {
    static template = xml`
        <div class="o-doc-sidebar position-sticky h-100 bg-1 border-right">
            <div>
                <input t-on-input="onSearchInput" class="w-100" placeholder="Search..."/>
            </div>
            <div class="o-doc-sidebar-content h-100 flex flex-column gap-1">
                <t t-foreach="state.visibleAddons" t-as="addon" t-key="addon.name">
                    <div
                        class="flex w-100 cursor-pointer capitalize user-select-none"
                        t-on-click="() => this.toggleAddon(addon.name)"
                        role="button"
                    >
                        <div class="icon-btn ps-1" role="button" t-att-class="{ o_collapsed: isCollapsed(addon.name)}">
                            <i class="fa fa-angle-right" aria-hidden="true"></i>
                        </div>
                        <h3 class="ms-1" t-out="addon.name"></h3>
                    </div>

                    <div t-if="!isCollapsed(addon.name)" class="ms-1 ps-1 border-left">
                        <t t-foreach="addon.models" t-as="model" t-key="model.model">
                            <a
                                class="btn block bg-none user-select-none"
                                href="#"
                                t-on-click="() => this.props.onModelSelected(model)"
                                t-att-class="{ o_active: isActiveItem(model) }"
                                role="button"
                            >
                                <div t-out="model.name"></div>
                                <small class="block" t-out="model.model"></small>
                            </a>
                        </t>
                    </div>
                </t>
            </div>
        </div>
    `;

    static components = {};
    static props = {
        activeModel: true,
        onModelSelected: true,
    };

    setup() {
        this.modelStore = useModelStore();
        this.state = useState({
            search: "",
            visibleAddons: this.props.addons,
            collapseAddons: {},
        });
        this.state.visibleAddons = this.filterAddons("");
    }

    onSearchInput(event) {
        this.state.search = event.target.value;
        this.state.visibleAddons = this.filterAddons(this.state.search);
    }

    toggleAddon(addonName) {
        this.state.collapseAddons[addonName] = !this.isCollapsed(addonName);
    }

    isCollapsed(addonName) {
        return this.state.collapseAddons[addonName];
    }

    isActiveItem(model) {
        return this.props.activeModel && model.name === this.props.activeModel.name && model.model == this.props.activeModel.model;
    }

    filterAddons(queryStr) {
        queryStr = queryStr.trim().toLocaleLowerCase();

        if (queryStr <= 0) {
            return this.modelStore.addons;
        } else {
            const visibleAddons = [];
            for (const addons of this.modelStore.addons) {
                let models = addons.models;
                if (!addons.name.includes(queryStr)) {
                    models = addons.models.filter(
                        (model) =>
                            model.name.toLowerCase().includes(queryStr) ||
                            model.model.toLowerCase().includes(queryStr)
                    );
                }
                if (models.length > 0) {
                    visibleAddons.push({
                        name: addons.name,
                        models,
                    });
                }
            }
            return visibleAddons;
        }
    }
}
