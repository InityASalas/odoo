import { _t } from "@web/core/l10n/translation";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { AvatarUserFormViewDialog } from "@mail/views/web/view_dialog/avatar_user_form_view_dialog";

export class Many2XAvatarUserAutocomplete extends Many2XAutocomplete {
    static components = {
        ...Many2XAutocomplete.components,
        CreateDialog: AvatarUserFormViewDialog,
    };

    slowCreate(request) {
        return this.openMany2X({
            context: this.getCreationContext(request),
            nextRecordsContext: this.props.context,
            title: _t("Invite teammates"),
        });
    }
}
