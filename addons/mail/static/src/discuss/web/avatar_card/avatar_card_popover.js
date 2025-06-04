import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";
import { useOpenChat } from "@mail/core/web/open_chat_hook";

export class AvatarCardPopover extends Component {
    static template = "mail.AvatarCardPopover";

    static props = {
        id: { type: Number, required: true },
        close: { type: Function, required: true },
    };

    setup() {
        this.actionService = useService("action");
        this.store = useService("mail.store");
        this.openChat = useOpenChat("res.users");
        onWillStart(async () => {
            await this.store.Persona.getAvatarCardData(this.props.id);
        });
    }

    get persona() {
        const persona = Object.values(this.store.Persona.records).filter(
            (x) => x.userId === this.props.id
        )[0];
        return persona;
    }

    get email() {
        return this.persona.email;
    }

    get phone() {
        return this.persona.phone;
    }

    get showViewProfileBtn() {
        return true;
    }

    get hasFooter() {
        return false;
    }

    async getProfileAction() {
        return {
            res_id: this.persona.id,
            res_model: "res.partner",
            type: "ir.actions.act_window",
            views: [[false, "form"]],
        };
    }

    get userId() {
        return this.persona.userId;
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
