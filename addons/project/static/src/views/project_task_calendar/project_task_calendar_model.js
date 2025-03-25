import { Domain } from "@web/core/domain";
import { serializeDate } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { CalendarModel } from '@web/views/calendar/calendar_model';

export class ProjectTaskCalendarModel extends CalendarModel {
    /**
     * @override
     */
    get defaultFilterLabel() {
        this.isCheckProject = 'project_id' in this.meta.filtersInfo;
        if (this.isCheckProject) {
            return _t("Private");
        }
        return super.defaultFilterLabel;
    }

    async load(params = {}) {
        return super.load({
            planTask: false,
            ...(params || {}),
        });
    }

    async loadRecords(data) {
        const [records] = await Promise.all([
            super.loadRecords(data),
            this.fetchTasksToPlan({ data }),
        ]);
        return records;
    }

    async fetchTasksToPlan(params) {
        if (this.meta.showTasksToPlan && !this.meta.planTask) {
            this.tasksToPlan = await this._fetchTasksToPlan(params);
        }
    }

    async loadMoreTasksToPlan() {
        const { records, length } = this.tasksToPlan;
        const offset = records.length;
        let limit = offset + 20;
        if (limit > length) {
            limit = length;
        }
        const { records: newRecords } = await this._fetchTasksToPlan({ limit, offset });
        this.tasksToPlan.records.push(...newRecords);
        this.notify();
    }

    async _fetchTasksToPlan({ data, limit, offset } = { limit: 20, offset: 0 }) {
        const projectId = this.meta.context.default_project_id;
        if (!projectId) {
            return [];
        }
        const { date_start, date_stop } = this.meta.fieldMapping;
        const fieldsToRemove = [...new Set([date_start, date_stop, 'planned_date_begin', 'date_deadline'])]
        let domain = Domain.removeDomainLeaves(
            Domain.and([
                this.meta.domain,
                this.computeFiltersDomain(data),
            ]),
            fieldsToRemove
        );
        domain = Domain.and([
            domain,
            [['planned_date_begin', '=', false], ['date_deadline', '=', false], ['project_id', '=', projectId]],
        ]);
        return await this.orm.webSearchRead(this.resModel, domain.toList(this.meta.context), {
            specification: {
                name: {},
            },
            limit,
            offset,
        });
    }

    _getPlanTaskVals(date, timeSlotSelected = false) {
        return { date_deadline: serializeDate(date) };
    }

    async planTask(taskId, date, timeSlotSelected = false) {
        this.tasksToPlan.length -= 1;
        this.tasksToPlan.records = this.tasksToPlan.records.filter((task) => task.id !== taskId);
        await this.orm.write(this.meta.resModel, [taskId], this._getPlanTaskVals(date, timeSlotSelected), {
            context: this.meta.context,
        });
        await this.load({ planTask: true });
    }
}
