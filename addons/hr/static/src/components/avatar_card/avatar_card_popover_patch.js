import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AvatarCardPopover } from "@mail/discuss/web/avatar_card/avatar_card_popover";

export const patchAvatarCardPopover = {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.userInfoTemplate = "hr.avatarCardUserInfos";
    },
    get mainEmployee() {
        if (this.persona.employee_ids?.length) {
            return this.persona.employee_ids[0];
        }
        if (this.persona.all_companies_employee_ids?.length) {
            return this.persona.all_companies_employee_ids[0];
        }
        return false;
    },
    get email() {
        return this.mainEmployee?.work_email || this.persona.email;
    },
    get phone() {
        return this.mainEmployee?.work_phone || this.persona.phone;
    },
    get workLocationType() {
        return this.mainEmployee?.work_location_type;
    },
    get workLocationName() {
        return this.mainEmployee?.work_location_name;
    },
    get jobTitle() {
        return this.mainEmployee?.job_title;
    },
    get departmentName() {
        return this.mainEmployee?.department_id?.name;
    },
    async getProfileAction() {
        return this.persona.employee_ids?.length > 0
            ? this.orm.call("hr.employee", "get_formview_action", [this.persona.employee_ids[0]])
            : super.getProfileAction(...arguments);
    },
};

export const unpatchAvatarCardPopover = patch(AvatarCardPopover.prototype, patchAvatarCardPopover);
