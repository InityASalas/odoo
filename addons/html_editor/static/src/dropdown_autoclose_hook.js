import { useEffect } from "@odoo/owl";

export function useDropdownAutoClose(overlayState, dropdownState) {
    if (!overlayState) {
        return;
    }
    useEffect(
        () => {
            if (!overlayState.isOverlayVisible) {
                dropdownState.close();
            }
        },
        () => [overlayState.isOverlayVisible]
    );
}
