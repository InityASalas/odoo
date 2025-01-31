import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ProductVariantPreview extends Interaction {
    static selector = ".o_wsale_attribute_previewer";
    // dynamicContent = {
    //     _window: {
    //         "t-on-resize": this.debounced(this.updateVariantPreview, 250),
    //     },
    // }

    setup() {
        this.updateVariantPreview()
    }

    updateVariantPreview(){
        const availableWidth = this.el.offsetWidth;
        let usedWidth = 0;
        // Class `gap-1` on parent adds 4px margin for each child element
        const margin = 4
        for (let child of this.el.children) {
            usedWidth += child.offsetWidth + margin;
        }
        let remainingCount = this.el.dataset.remainingCount ?? 0

        while (usedWidth > availableWidth) {
            const childToRemove = this.el.lastElementChild;
            usedWidth -= childToRemove.offsetWidth + margin;
            remainingCount++;
            this.el.removeChild(childToRemove);
        }
        if (remainingCount > 0) {
            // Remove last element to add span in its place
            this.el.removeChild(this.el.lastElementChild);
            remainingCount++;
            const spanElement = document.createElement('span');
            const anchorElement = document.createElement('a');
            anchorElement.href = this.el.dataset.productHref;
            anchorElement.textContent = `+${remainingCount}`;
            anchorElement.classList.add('ms-1','small');
            spanElement.appendChild(anchorElement);
            this.el.appendChild(spanElement);
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
