import {
    Component,
    onMounted,
    onPatched,
    onWillUnmount,
    useEffect,
    useRef,
    useState,
} from "@odoo/owl";
import { hasTouch } from "@web/core/browser/feature_detection";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { hidePDFJSButtons } from "@web/core/utils/pdfjs";
import { throttleForAnimation } from "@web/core/utils/timing";

/**
 * @typedef {Object} File
 * @property {string} name
 * @property {string} downloadUrl
 * @property {boolean} [isImage]
 * @property {boolean} [isPdf]
 * @property {boolean} [isVideo]
 * @property {boolean} [isText]
 * @property {string} [defaultSource]
 * @property {boolean} [isUrlYoutube]
 * @property {string} [mimetype]
 * @property {boolean} [isViewable]
 * @typedef {Object} Props
 * @property {Array<File>} files
 * @property {number} startIndex
 * @property {function} close
 * @property {boolean} [modal]
 * @extends {Component<Props, Env>}
 */
export class FileViewer extends Component {
    static template = "web.FileViewer";
    static components = {};
    static props = ["files", "startIndex", "close?", "modal?"];
    static defaultProps = {
        modal: true,
    };

    setup() {
        this.hasTouch = hasTouch();
        useAutofocus();
        this.imageRef = useRef("image");
        this.zoomerRef = useRef("zoomer");
        this.zoomerPadding = { vertical: null, horizontal: null };
        this.iframeViewerPdfRef = useRef("iframeViewerPdf");

        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;

        this.scrollZoomStep = 0.1;
        this.zoomStep = 0.5;
        this.minScale = 0.5;
        this.translate = {
            dx: 0,
            dy: 0,
            x: 0,
            y: 0,
        };
        this.throttledUpdateImageDrag = throttleForAnimation(this.updateImageDrag.bind(this));

        this.state = useState({
            index: this.props.startIndex,
            file: this.props.files[this.props.startIndex],
            imageLoaded: false,
            scale: 1,
            angle: 0,
        });
        this.ui = useService("ui");
        useEffect(
            (el) => {
                if (el) {
                    hidePDFJSButtons(this.iframeViewerPdfRef.el, {
                        hideDownload: true,
                        hidePrint: true,
                    });
                }
            },
            () => [this.iframeViewerPdfRef.el]
        );
        onPatched(() => {
            if (this.zoomerPadding.vertical != null) return;
            if (this.zoomerRef.el) {
                const style = getComputedStyle(this.zoomerRef.el);
                this.zoomerPadding.vertical = 2 * parseFloat(style.paddingTop) + 20;
                this.zoomerPadding.horizontal = 2 * parseFloat(style.paddingLeft) + 20;
            }
        });
        if (this.hasTouch) {
            this.throttledUpdateImagePinch = throttleForAnimation(this.updateImagePinch.bind(this));
            this.boundOnTouchstartImage = this.onTouchstartImage.bind(this);
            this.boundOnTouchendImage = this.onTouchendImage.bind(this);
            this.boundOnTouchmoveImage = this.onTouchmoveImage.bind(this);
            this.prevImageRef = null;
            onMounted(() => {
                if (!this.imageRef.el) return;
                this.prevImageRef = this.imageRef.el;
                this.imageRef.el.addEventListener("touchstart", this.boundOnTouchstartImage);
                this.imageRef.el.addEventListener("touchmove", this.boundOnTouchmoveImage);
                this.imageRef.el.addEventListener("touchend", this.boundOnTouchendImage);
            });
            onPatched(() => {
                if (this.imageRef.el == this.prevImageRef) return;
                if (this.prevImageRef) {
                    this.prevImageRef.removeEventListener(
                        "touchstart",
                        this.boundOnTouchstartImage
                    );
                    this.prevImageRef.removeEventListener("touchmove", this.boundOnTouchmoveImage);
                    this.prevImageRef.removeEventListener("touchend", this.boundOnTouchendImage);
                }
                if (this.imageRef.el) {
                    this.imageRef.el.addEventListener("touchstart", this.boundOnTouchstartImage);
                    this.imageRef.el.addEventListener("touchmove", this.boundOnTouchmoveImage);
                    this.imageRef.el.addEventListener("touchend", this.boundOnTouchendImage);
                }
                this.prevImageRef = this.imageRef.el;
            });
            onWillUnmount(() => {
                if (!this.imageRef.el) return;
                this.imageRef.el.removeEventListener("touchstart", this.boundOnTouchstartImage);
                this.imageRef.el.removeEventListener("touchmove", this.boundOnTouchmoveImage);
                this.imageRef.el.removeEventListener("touchend", this.boundOnTouchendImage);
            });
        }
    }

    onImageLoaded() {
        this.state.imageLoaded = true;
    }

    close() {
        this.props.close && this.props.close();
    }

    next() {
        const last = this.props.files.length - 1;
        this.activateFile(this.state.index === last ? 0 : this.state.index + 1);
    }

    previous() {
        const last = this.props.files.length - 1;
        this.activateFile(this.state.index === 0 ? last : this.state.index - 1);
    }

    activateFile(index) {
        this.state.index = index;
        this.state.file = this.props.files[index];
    }

    onKeydown(ev) {
        switch (ev.key) {
            case "ArrowRight":
                this.next();
                break;
            case "ArrowLeft":
                this.previous();
                break;
            case "Escape":
                this.close();
                break;
            case "q":
                this.close();
                break;
        }
        if (this.state.file.isImage) {
            switch (ev.key) {
                case "r":
                    this.rotate();
                    break;
                case "+":
                    this.zoomIn();
                    break;
                case "-":
                    this.zoomOut();
                    break;
                case "0":
                    this.resetZoom();
                    break;
            }
        }
    }

    /**
     * @param {WheelEvent} ev
     */
    onWheelImage(ev) {
        if (ev.deltaY > 0) {
            this.zoomOut({ scroll: true });
        } else {
            this.zoomIn({ scroll: true });
        }
    }

    /**
     * @param {MouseEvent} ev
     */
    onMousedownImage(ev) {
        if (ev.button !== 0) return;
        this.startImageDrag(ev);
    }

    /**
     * @param {MouseEvent} ev
     */
    onMousemoveImage(ev) {
        this.throttledUpdateImageDrag(ev);
    }

    /**
     * @param {MouseEvent} ev
     */
    onMouseupImage(ev) {
        this.endImageDrag(ev);
    }

    /**
     * @param {TouchEvent} ev
     */
    onTouchstartImage(ev) {
        if (ev.touches.length === 2) {
            this.startImagePinch(ev);
        } else if (ev.touches.length === 1) {
            this.startImageDrag(ev);
        }
    }

    /**
     * @param {TouchEvent} ev
     */
    onTouchmoveImage(ev) {
        if (ev.touches.length === 2) {
            this.throttledUpdateImagePinch(ev);
        } else if (ev.touches.length === 1) {
            this.throttledUpdateImageDrag(ev);
        }
    }

    /**
     * @param {TouchEvent} ev
     */
    onTouchendImage(ev) {
        if (ev.touches.length < 2) {
            this.endImagePinch();
            this.endImageDrag(ev);
        }
    }

    /**
     * @param {TouchEvent | MouseEvent} ev
     */
    startImageDrag(ev) {
        this.isDragging = true;
        const { clientX, clientY } = ev instanceof MouseEvent ? ev : ev.touches[0];
        this.dragStartX = clientX;
        this.dragStartY = clientY;
    }

    /**
     * @param {TouchEvent | MouseEvent} ev
     */
    updateImageDrag(ev) {
        if (!this.isDragging) return;
        if (ev.touches && ev.touches.length > 1) return;
        const { clientX, clientY } = ev instanceof MouseEvent ? ev : ev.touches[0];
        this.translate.dx = clientX - this.dragStartX;
        this.translate.dy = clientY - this.dragStartY;
        const { didClampX, didClampY } = this.updateZoomerStyle();
        if (didClampX) this.dragStartX = clientX;
        if (didClampY) this.dragStartY = clientY;
    }

    /**
     * @param {TouchEvent | MouseEvent} ev
     */
    endImageDrag(ev) {
        if (!this.isDragging) return;
        if (ev.touches && ev.touches.length > 0) return;
        this.isDragging = false;
        this.translate.x += this.translate.dx;
        this.translate.y += this.translate.dy;
        this.translate.dx = 0;
        this.translate.dy = 0;
        this.updateZoomerStyle();
    }

    /**
     * @param {TouchEvent} ev
     */
    startImagePinch(ev) {
        this.isDragging = false;
        this.lastPinchDistance = this.getPinchDistance(ev.touches);
    }

    /**
     * @param {TouchEvent} ev
     */
    updateImagePinch(ev) {
        if (!this.lastPinchDistance) return;
        const currentDistance = this.getPinchDistance(ev.touches);
        const zoomFactor = currentDistance / this.lastPinchDistance;
        this.state.scale = Math.max(this.minScale, this.state.scale * zoomFactor);
        this.lastPinchDistance = currentDistance;
        this.updateZoomerStyle();
    }

    endImagePinch() {
        this.lastPinchDistance = null;
    }

    /**
     * @param {TouchList} touches
     */
    getPinchDistance(touches) {
        const [touch1, touch2] = touches;
        const dx = touch2.clientX - touch1.clientX;
        const dy = touch2.clientY - touch1.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    resetZoom() {
        this.state.scale = 1;
        this.updateZoomerStyle();
    }

    rotate() {
        this.state.angle += 90;
        this.updateZoomerStyle();
    }

    /**
     * @param {{ scroll?: boolean }}
     */
    zoomIn({ scroll = false } = {}) {
        this.state.scale = this.state.scale + (scroll ? this.scrollZoomStep : this.zoomStep);
        this.updateZoomerStyle();
    }

    /**
     * @param {{ scroll?: boolean }}
     */
    zoomOut({ scroll = false } = {}) {
        if (this.state.scale === this.minScale) {
            return;
        }
        const unflooredAdaptedScale =
            this.state.scale - (scroll ? this.scrollZoomStep : this.zoomStep);
        this.state.scale = Math.max(this.minScale, unflooredAdaptedScale);
        this.updateZoomerStyle();
    }

    updateZoomerStyle() {
        const isImageRotated = [90, 360].includes(this.state.angle % 360);
        const imageEl = this.imageRef.el;
        const zoomerEl = this.zoomerRef.el;
        const imageWidth =
            (isImageRotated ? imageEl.offsetHeight : imageEl.offsetWidth) * this.state.scale;
        const imageHeight =
            (isImageRotated ? imageEl.offsetWidth : imageEl.offsetHeight) * this.state.scale;
        const containerWidth = zoomerEl.offsetWidth - this.zoomerPadding.horizontal;
        const containerHeight = zoomerEl.offsetHeight - this.zoomerPadding.vertical;
        let translateX = imageWidth > containerWidth ? this.translate.x + this.translate.dx : 0;
        const maxTranslateX = (imageWidth - containerWidth) / 2;
        const minTranslateX = -maxTranslateX;
        let didClampX = false;
        if (translateX === 0) {
            this.translate.x = 0;
        } else if (translateX > maxTranslateX) {
            translateX = maxTranslateX;
            this.translate.x = translateX;
            didClampX = true;
        } else if (translateX < minTranslateX) {
            translateX = minTranslateX;
            this.translate.x = translateX;
            didClampX = true;
        }
        let translateY = imageHeight > containerHeight ? this.translate.y + this.translate.dy : 0;
        const maxTranslateY = (imageHeight - containerHeight) / 2;
        const minTranslateY = -maxTranslateY;
        let didClampY = false;
        if (translateY === 0) {
            this.translate.y = 0;
        } else if (translateY > maxTranslateY) {
            translateY = maxTranslateY;
            this.translate.y = translateY;
            didClampY = true;
        } else if (translateY < minTranslateY) {
            translateY = minTranslateY;
            this.translate.y = translateY;
            didClampY = true;
        }
        zoomerEl.style.transform = `translate3d(${translateX}px, ${translateY}px, 0px)`;
        return { didClampX, didClampY };
    }

    get rotationStyle() {
        return `transform: rotate(${this.state.angle}deg);`;
    }

    get imageStyle() {
        let style = "transform: " + `scale3d(${this.state.scale}, ${this.state.scale}, 1);`;

        if (this.state.angle % 180 !== 0) {
            style += `max-height: ${window.innerWidth}px; max-width: ${window.innerHeight}px;`;
        } else {
            style += "max-height: 100%; max-width: 100%;";
        }
        style += `background: repeating-conic-gradient(#ccc 0deg 90deg, #fff 90deg 180deg) 50% / 20px 20px;`;
        return style;
    }

    onClickPrint() {
        const printWindow = window.open("about:blank", "_new");
        printWindow.document.open();
        printWindow.document.write(`
                <html>
                    <head>
                        <script>
                            function onloadImage() {
                                setTimeout('printImage()', 10);
                            }
                            function printImage() {
                                window.print();
                                window.close();
                            }
                        </script>
                    </head>
                    <body onload='onloadImage()'>
                        <img src="${this.state.file.defaultSource}" alt=""/>
                    </body>
                </html>`);
        printWindow.document.close();
    }
}
