import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { getScrollingElement } from "@web/core/utils/scrolling";
import { AnimateOption } from "./animate_option";
import { ANIMATE } from "@website/builder/option_sequence";
import { BuilderAction } from "@html_builder/core/core_builder_action_plugin";

class AnimateOptionPlugin extends Plugin {
    static id = "animateOption";
    static dependencies = ["imageToolOption"];
    resources = {
        builder_options: [
            withSequence(ANIMATE, {
                OptionComponent: AnimateOption,
                selector: ".o_animable, section .row > div, img, .fa, .btn, .o_animated_text",
                exclude:
                    "[data-oe-xpath], .o_not-animable, .s_col_no_resize.row > div, .s_col_no_resize",
                props: {
                    getDirectionsItems: this.getDirectionsItems.bind(this),
                    getEffectsItems: this.getEffectsItems.bind(this),
                    canHaveHoverEffect: this.dependencies.imageToolOption.canHaveHoverEffect,
                },
                // todo: to implement
                // textSelector: ".o_animated_text",
            }),
        ],
        system_classes: ["o_animating"],
        builder_actions: {
            setAnimationMode: new SetAnimationModeAction(this),
            setAnimateIntensity: new SetAnimateIntensityAction(this),
            forceAnimation: new ForceAnimationAction(this),
            setAnimationEffect: new SetAnimationEffectAction(this),
        },
        normalize_handlers: this.normalize.bind(this),
        clean_for_save_handlers: this.cleanForSave.bind(this),
    };

    setup() {
        this.scrollingElement = getScrollingElement(this.document);
    }

    getEffectsItems(isActiveItem) {
        const isOnAppearance = () => isActiveItem("animation_on_appearance_opt");
        return [
            { className: "o_anim_fade_in", label: "Fade" },
            { className: "o_anim_slide_in", label: "Slide", directionClass: "o_anim_from_right" },
            { className: "o_anim_bounce_in", label: "Bounce" },
            { className: "o_anim_rotate_in", label: "Rotate" },
            { className: "o_anim_zoom_out", label: "Zoom Out" },
            { className: "o_anim_zoom_in", label: "Zoom In" },
            { className: "o_anim_flash", label: "Flash", check: isOnAppearance },
            { className: "o_anim_pulse", label: "Pulse", check: isOnAppearance },
            { className: "o_anim_shake", label: "Shake", check: isOnAppearance },
            { className: "o_anim_tada", label: "Tada", check: isOnAppearance },
            { className: "o_anim_flip_in_x", label: "Flip-In-X", check: isOnAppearance },
            { className: "o_anim_flip_in_y", label: "Flip-In-Y", check: isOnAppearance },
        ];
    }
    getDirectionsItems() {
        const isNotSlideIn = (editingElement) =>
            !editingElement.classList.contains("o_anim_slide_in");
        const isRotate = (editingElement) => editingElement.classList.contains("o_anim_rotate_in");
        const isNotRotate = (editingElement) => !isRotate(editingElement);

        return [
            { className: "", label: "In place", check: isNotSlideIn },

            { className: "o_anim_from_right", label: "From right", check: isNotRotate },
            { className: "o_anim_from_left", label: "From left", check: isNotRotate },
            { className: "o_anim_from_bottom", label: "From bottom", check: isNotRotate },
            { className: "o_anim_from_top", label: "From top", check: isNotRotate },

            { className: "o_anim_from_top_right", label: "From top right", check: isRotate },
            { className: "o_anim_from_top_left", label: "From top left", check: isRotate },
            { className: "o_anim_from_bottom_right", label: "From bottom right", check: isRotate },
            { className: "o_anim_from_bottom_left", label: "From bottom left", check: isRotate },
        ];
    }
    async forceAnimation(editingElement) {
        editingElement.style.animationName = "dummy";
        if (editingElement.classList.contains("o_animate_on_scroll")) {
            // Trigger a DOM reflow.
            void editingElement.offsetWidth;
            editingElement.style.animationName = "";
            this.window.dispatchEvent(new Event("resize"));
        } else {
            // Trigger a DOM reflow (Needed to prevent the animation from
            // being launched twice when previewing the "Intensity" option).
            await new Promise((resolve) => setTimeout(resolve));
            editingElement.classList.add("o_animating");
            this.scrollingElement.classList.add("o_wanim_overflow_xy_hidden");
            editingElement.style.animationName = "";
            editingElement.addEventListener(
                "animationend",
                () => {
                    this.scrollingElement.classList.remove("o_wanim_overflow_xy_hidden");
                    editingElement.classList.remove("o_animating");
                },
                { once: true }
            );
        }
    }

    normalize(root) {
        const previewEls = [...root.querySelectorAll(".o_animate_preview")];
        if (root.classList.contains("o_animate_preview")) {
            previewEls.push(root);
        }
        for (const el of previewEls) {
            if (el.classList.contains("o_animate")) {
                el.classList.remove("o_animate_preview");
            }
        }

        const animateEls = [...root.querySelectorAll(".o_animate")];
        if (root.classList.contains("o_animate")) {
            animateEls.push(root);
        }
        for (const el of animateEls) {
            if (!el.classList.contains("o_animate_preview")) {
                el.classList.add("o_animate_preview");
            }
        }
        const animateImg = animateEls
            .map((el) => (el.tagName === "IMG" && el) || el.querySelectorAll("img"))
            .flat()
            .filter(Boolean);
        for (const img of animateImg) {
            img.loading = "eager";
        }
    }
    cleanForSave({ root }) {
        for (const el of root.querySelectorAll(".o_animate_preview")) {
            el.classList.remove("o_animate_preview");
        }
    }
}

class SetAnimationModeAction extends BuilderAction {
    setup() {
        this.animationWithFadein = ["onAppearance", "onScroll"];
    }
    // todo: to remove after having the commit of louis
    isApplied() {
        return true;
    }
    clean({ editingElement, value: effectName, nextAction }) {
        this.plugin.scrollingElement.classList.remove("o_wanim_overflow_xy_hidden");
        editingElement.classList.remove(
            "o_animating",
            "o_animate_both_scroll",
            "o_visible",
            "o_animated",
            "o_animate_out"
        );
        editingElement.style.animationDelay = "";
        editingElement.style.animationPlayState = "";
        editingElement.style.animationName = "";
        editingElement.style.visibility = "";

        if (effectName === "onScroll") {
            delete editingElement.dataset.scrollZoneStart;
            delete editingElement.dataset.scrollZoneEnd;
        }
        if (effectName === "onHover") {
            // todo: to implement
            // this.trigger_up("option_update", {
            //     optionName: "ImageTools",
            //     name: "disable_hover_effect",
            // });
        }

        const isNextAnimationFadein = this.animationWithFadein.includes(nextAction.value);
        if (!isNextAnimationFadein) {
            this._removeEffectAndDirectionClasses(editingElement.classList);
            editingElement.style.setProperty("--wanim-intensity", "");
            editingElement.style.animationDuration = "";
            this._setImagesLazyLoading(editingElement);
        }
    }
    apply({ editingElement, value: effectName, params: { forceAnimation } }) {
        if (this.animationWithFadein.includes(effectName)) {
            editingElement.classList.add("o_anim_fade_in");
        }
        if (effectName === "onScroll") {
            editingElement.dataset.scrollZoneStart = 0;
            editingElement.dataset.scrollZoneEnd = 100;
        }
        if (effectName === "onHover") {
            // todo: to implement
            // Pause the history until the hover effect is applied in
            // "setImgShapeHoverEffect". This prevents saving the intermediate
            // steps done (in a tricky way) up to that point.
            // this.options.wysiwyg.odooEditor.historyPauseSteps();
            // this.trigger_up("option_update", {
            //     optionName: "ImageTools",
            //     name: "enable_hover_effect",
            // });
        }
        if (forceAnimation) {
            this.plugin.forceAnimation(editingElement);
        }
    }
    /**
     * Adds the lazy loading on images because animated images can appear before
     * or after their parents and cause bugs in the animations. To put "lazy"
     * back on the "loading" attribute, we simply remove the attribute as it is
     * automatically added on page load.
     *
     * @private
     */
    _setImagesLazyLoading(editingElement) {
        const imgEls = editingElement.matches("img")
            ? [editingElement]
            : editingElement.querySelectorAll("img");
        for (const imgEl of imgEls) {
            // Let the automatic system add the loading attribute
            imgEl.removeAttribute("loading");
        }
    }
    _removeEffectAndDirectionClasses(targetClassList) {
        const classes = this.plugin
            .getEffectsItems()
            .map(({ className }) => className)
            .concat(
                this.plugin
                    .getDirectionsItems()
                    .map(({ className }) => className)
                    .filter(Boolean)
            );

        const classesToRemove = intersect(classes, [...targetClassList]);
        for (const className of classesToRemove) {
            targetClassList.remove(className);
        }
    }
}
class SetAnimateIntensityAction extends BuilderAction {
    getValue({ editingElement }) {
        const intensity = parseInt(
            this.window.getComputedStyle(editingElement).getPropertyValue("--wanim-intensity")
        );
        return intensity;
    }
    apply({ editingElement, value }) {
        editingElement.style.setProperty("--wanim-intensity", `${value}`);
        this.plugin.forceAnimation(editingElement);
    }
}
class ForceAnimationAction extends BuilderAction {
    // todo: to remove after having the commit of louis
    isActive() {
        return true;
    }
    apply({ editingElement }) {
        this.plugin.forceAnimation(editingElement);
    }
}
class SetAnimationEffectAction extends BuilderAction {
    isApplied({ editingElement, value: className }) {
        return editingElement.classList.contains(className);
    }
    clean({ editingElement }) {
        const classNames = this.plugin
            .getEffectsItems()
            .map(({ className }) => className)
            .concat(this.plugin.getDirectionsItems().map(({ className }) => className));
        for (const className of classNames) {
            if (editingElement.classList.contains(className)) {
                editingElement.classList.remove(className);
            }
        }
    }
    apply({ editingElement, params: { mainParam: directionClassName }, value: effectClassName }) {
        if (directionClassName) {
            editingElement.classList.add(directionClassName);
        }
        editingElement.classList.add(effectClassName);
        this.plugin.forceAnimation(editingElement);
    }
}

registry.category("website-plugins").add(AnimateOptionPlugin.id, AnimateOptionPlugin);

function intersect(a, b) {
    return a.filter((value) => b.includes(value));
}
