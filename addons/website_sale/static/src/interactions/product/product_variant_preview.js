import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ProductVariantPreview extends Interaction {
    static selector = ".o_wsale_attribute_previewer";
    dynamicContent = {
        _window: {
            "t-on-resize": this.debounced(this.updateVariantPreview, 250),
        },
    };

    setup() {
        this.ptavs = [...this.el.children];
        this.indicatorSpan = this.ptavs.splice(this.ptavs.length - 1, 1)[0];
        this.ptavCount = this.ptavs.length + Number(this.el.dataset.remainingCount ?? 0);
        this.updateVariantPreview();
    }
    resetDisplay() {
        for (const child of this.el.children) {
            child.classList.add('d-none');
        }
    }
    showRemainingCountIndicator(count) {
        this.indicatorSpan.firstElementChild.textContent = `+${count}`;
        this.indicatorSpan.classList.remove('d-none');
    }
    updateVariantPreview() {
        this.resetDisplay();
        const availableWidth = this.el.offsetWidth;
        let usedWidth = 0;
        let displayedPTAVs = 0;
        // Class `gap-1` on parent adds 4px margin for each ptav
        const margin = 4;
        for (const ptav of this.ptavs) {
            ptav.classList.remove('d-none');
            usedWidth += ptav.offsetWidth + margin;
            displayedPTAVs++;
            if (usedWidth >= availableWidth) {
                // 2 elements are removed, the overflowing element and previous element to make
                // space for span to be added
                ptav.classList.add('d-none');
                ptav.previousElementSibling.classList.add('d-none');
                displayedPTAVs -= 2;
                const remainingCount = this.ptavCount - displayedPTAVs;
                this.showRemainingCountIndicator(remainingCount);
                break;
            }
            // If last element in array check if there is hidden remaining elements from backend
            const isLastPTAV = ptav === this.ptavs[this.ptavs.length - 1];
            if (isLastPTAV && this.ptavCount > displayedPTAVs) {
                const indicatorSpanSize = 25;
                if (usedWidth + indicatorSpanSize >= availableWidth) {
                    ptav.classList.add('d-none');
                    displayedPTAVs--;
                }
                this.showRemainingCountIndicator(this.ptavCount - displayedPTAVs);
            }
        }


    }
}

export class ProductVariantPreviewImageHover extends Interaction {
    static selector = ".oe_product_cart";
    dynamicContent = {
        '.o_product_variant_preview': {
            "t-on-mouseenter": this.mouseEnter,
            "t-on-mouseleave": this.mouseLeave,
        },
    };

    setup() {
        this.productImg = this.el.querySelector(".oe_product_image_img_wrapper img");
        this.originalImgSrc = this.productImg.getAttribute("src");
        this.variantImageSrc = null;
    }

    mouseEnter(ev) {
        this.variantImageSrc = ev.target.dataset.variantImage;
        if (!this.variantImageSrc) {
            return;
        }
        this.setImgSrc(this.variantImageSrc);
    }

    mouseLeave() {
        this.setImgSrc(this.originalImgSrc);
    }

    setImgSrc(imageSrc) {
        this.productImg.src = imageSrc;
    }
}

registry
    .category("public.interactions")
    .add("website_sale.product_variant_preview", ProductVariantPreview);
registry
    .category("public.interactions")
    .add("website_sale.product_variant_preview_image_hover", ProductVariantPreviewImageHover);
