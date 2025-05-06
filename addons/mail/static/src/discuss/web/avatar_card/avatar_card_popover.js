import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";
import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { useOpenChat } from "@mail/core/web/open_chat_hook";

export class AvatarCardPopover extends Component {
    static template = "mail.AvatarCardPopover";

    static props = {
        id: { type: Number, required: true },
        close: { type: Function, required: true },
    };

    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.openChat = useOpenChat("res.users");
        this.state = useState({
            showUserTime: false,
            userTime: null,
            userDate: null,
            userTz: null
        });
        let intervalId;
        let timeoutId;
        const currentLanguage = (session.bundle_params.lang || "en-US").replace("_", "-");
        const updateDisplayedTime = (currentUserTz, targetUserTz) => {
            const now = new Date();
            const currentTime = new Intl.DateTimeFormat(currentLanguage, {
                hour: "2-digit",
                minute: "2-digit",
                timeZone: targetUserTz
            }).format(now);
            const currentUserDate = new Intl.DateTimeFormat(currentLanguage, {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                timeZone: currentUserTz
            }).format(now);
            const targetUserDate = new Intl.DateTimeFormat(currentLanguage, {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                timeZone: targetUserTz
            }).format(now);
            this.state.showUserTime = true;
            this.state.userTime = currentTime;
            this.state.userTz = targetUserTz;
            this.state.userDate = currentUserDate !== targetUserDate ? targetUserDate : null;
        };
        onWillStart(async () => {
            let targetUserTz;
            const recordModel = this.props.recordModel || "res.users";
            [this.user] = await this.orm.read(recordModel, [this.props.id], this.fieldNames);
            targetUserTz = this.user.tz || null;
            const currentPartner = Object.values(session.storeData?.["res.partner"] || {}).find(p => p.active);
            const currentUserTz = currentPartner?.tz || null;
            if (targetUserTz && currentUserTz && targetUserTz !== currentUserTz) {
                updateDisplayedTime(currentUserTz, targetUserTz);
                const msUntilNextMinute = 60000 - (Date.now() % 60000);
                timeoutId = setTimeout(() => {
                    updateDisplayedTime(currentUserTz, targetUserTz);
                    intervalId = setInterval(() => {
                        updateDisplayedTime(currentUserTz, targetUserTz);
                    }, 60000);
                }, msUntilNextMinute);
            }
        });
        onWillUnmount(() => {
            if (intervalId) clearInterval(intervalId);
            if (timeoutId) clearTimeout(timeoutId);
        });
    }

    get fieldNames() {
        return ["name", "email", "phone", "im_status", "share", "partner_id", "tz"];
    }

    get email() {
        return this.user.email;
    }

    get phone() {
        return this.user.phone;
    }

    get showViewProfileBtn() {
        return true;
    }

    get hasFooter() {
        return false;
    }

    async getProfileAction() {
        return {
            res_id: this.user.partner_id[0],
            res_model: "res.partner",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
        };
    }

    get userId() {
        return this.user.id;
    }

    onSendClick() {
        this.openChat(this.userId);
        this.props.close();
    }

    async onClickViewProfile(newWindow) {
        const action = await this.getProfileAction();
        this.actionService.doAction(action, { newWindow });
    }
}
