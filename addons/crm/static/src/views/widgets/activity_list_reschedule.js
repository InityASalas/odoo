import { ActivityListRescheduleDropdown } from "@mail/views/web/list/activity_list_reschedule";
import { onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

export class CRMActivityRescheduleDropdown extends ActivityListRescheduleDropdown {
    static template = "crm.CRMActivityRescheduleDropdown";

    setup() {
        super.setup();
        this.targetDays.today.actionName = "action_reschedule_my_next_today";
        this.targetDays.tomorrow.actionName = "action_reschedule_my_next_tomorrow";
        this.targetDays.nextWeek.actionName = "action_reschedule_my_next_nextweek";

        onWillStart(async () => {
            this.isAllowedDisplay = await user.hasGroup("base.group_user");
        })
    }

    async actionRescheduleMeeting() {
        await this.action.doActionButton({
            type: "object",
            name: "action_reschedule_meeting",
            resModel: this.props.record.resModel,
            resId: this.props.record.resId,
            resIds: this.props.record.resIds,
        });
    }
}

registry.category("view_widgets").add("crm_activity_reschedule_dropdown", {
    component: CRMActivityRescheduleDropdown,
    extractProps: ({ attrs }) => {
        const { readonly } = attrs;
        return {
            readonly,
        };
    },
});
