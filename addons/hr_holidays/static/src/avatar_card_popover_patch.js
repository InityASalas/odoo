import { AvatarCardPopover } from "@mail/discuss/web/avatar_card/avatar_card_popover";

import { patch } from "@web/core/utils/patch";

patch(AvatarCardPopover.prototype, {
    get outOfOfficeDateEndText() {
        return this.persona.outOfOfficeDateEndText ?? "";
    },
});
