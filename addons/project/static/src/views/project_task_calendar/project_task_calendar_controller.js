import { _t } from "@web/core/l10n/translation";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { subTaskDeleteConfirmationMessage } from "@project/views/project_task_form/project_task_form_controller";
import { ProjectTaskCalendarSidePanel } from "./side_panel/project_task_calendar_side_panel";

export class ProjectTaskCalendarController extends CalendarController {
    static components = {
        ...ProjectTaskCalendarController.components,
        CalendarSidePanel: ProjectTaskCalendarSidePanel,
    };

    get modelParams() {
        return {
            ...super.modelParams,
            showTasksToPlan: this.canDragAndDropRecord,
        }
    }

    get editRecordDefaultDisplayText() {
        return _t("New Task");
    }

    get sidePanelProps() {
        return {
            ...super.sidePanelProps,
            editRecord: this.editRecord.bind(this),
        };
    }

    deleteConfirmationDialogProps(record) {
        const deleteConfirmationDialogProps = super.deleteConfirmationDialogProps(record);
        if  (!record.rawRecord.subtask_count) {
            return deleteConfirmationDialogProps;
        }

        return {
            ...deleteConfirmationDialogProps,
            body: subTaskDeleteConfirmationMessage,
        }
    }
}
