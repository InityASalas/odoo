import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";
import { normalizeColor } from "@html_builder/utils/utils_css";
import { defaultImageFilterOptions } from "@html_editor/main/media/image_post_process_plugin";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";

class ImageFilterOptionPlugin extends Plugin {
    static id = "ImageFilterOption";
    static dependencies = ["imagePostProcess"];
    resources = {
        builder_actions: {
            glFilter: new GlFilterAction(this),
            setCustomFilter: new SetCustomFilterAction(this),
        },
    };
}

class GlFilterAction extends BuilderAction {
    isApplied({ editingElement, params: { mainParam: glFilterName } }) {
        if (glFilterName) {
            return editingElement.dataset.glFilter === glFilterName;
        } else {
            return !editingElement.dataset.glFilter;
        }
    }
    async load({ editingElement: img, params: { mainParam: glFilterName } }) {
        return await this.dependencies.imagePostProcess.processImage({
            img,
            newDataset: {
                glFilter: glFilterName,
            },
        });
    }
    apply({ loadResult: updateImageAttributes }) {
        updateImageAttributes();
    }
}
class SetCustomFilterAction extends BuilderAction {
    getValue({ editingElement, params: { mainParam: filterProperty } }) {
        const filterOptions = JSON.parse(editingElement.dataset.filterOptions || "{}");
        return filterOptions[filterProperty] || defaultImageFilterOptions[filterProperty];
    }
    isApplied({ editingElement, params: { mainParam: filterProperty }, value: filterValue }) {
        const filterOptions = JSON.parse(editingElement.dataset.filterOptions || "{}");
        return (
            filterValue ===
            (filterOptions[filterProperty] || defaultImageFilterOptions[filterProperty])
        );
    }
    async load({ editingElement: img, params: { mainParam: filterProperty }, value }) {
        const filterOptions = JSON.parse(img.dataset.filterOptions || "{}");
        filterOptions[filterProperty] =
            filterProperty === "filterColor" ? normalizeColor(value) : value;
        return this.dependencies.imagePostProcess.processImage({
            img,
            newDataset: {
                filterOptions: JSON.stringify(filterOptions),
            },
        });
    }
    apply({ loadResult: updateImageAttributes }) {
        updateImageAttributes();
    }
}

registry.category("website-plugins").add(ImageFilterOptionPlugin.id, ImageFilterOptionPlugin);
