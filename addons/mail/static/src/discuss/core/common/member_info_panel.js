import { ImStatus } from "@mail/core/common/im_status";
import { ActionPanel } from "@mail/discuss/core/common/action_panel";
import { AttachmentList } from "@mail/core/common/attachment_list";

import { Component } from "@odoo/owl";

import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ChannelMemberInfo extends Component {
    static components = { ImStatus, ActionPanel, AttachmentList };
    static props = ["thread", "attachmentAction"];
    static template = "discuss.ChannelMemberInfo";

    setup() {
        this.rtc = useService("discuss.rtc");
        this.actionsService = useService("action");
    }

    get correspondent() {
        return this.props.thread.correspondent;
    }

    get thread() {
        return this.props.thread;
    }

    openUserRecord() {
        this.actionsService.doAction({
            type: "ir.actions.act_window",
            res_model: "res.partner",
            views: [[false, "form"]],
            res_id: this.correspondent.persona.id,
        });
    }

    /** List of the keys that define correspondent info */
    get correspondentInfoKeys() {
        return ["email", "phone"];
    }

    get correspondentInfo() {
        return this.correspondentInfoKeys.map((key) => ({
            key: _t("%(label)s", { label: this._formatKey(key) }),
            value: this.correspondent.persona[key],
        }));
    }

    _formatKey(key) {
        return key.replace(/_/g, "").replace(/\b\w/g, (char) => char.toUpperCase());
    }
}
