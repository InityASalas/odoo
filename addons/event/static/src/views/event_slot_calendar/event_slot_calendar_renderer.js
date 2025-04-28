import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";
import { CalendarRenderer } from "@web/views/calendar/calendar_renderer";
import { CalendarYearRenderer } from "@web/views/calendar/calendar_year/calendar_year_renderer";

import { useEffect } from "@odoo/owl";

export class EventSlotCalendarCommonRenderer extends CalendarCommonRenderer {
    // Display end time and hide title on the full calendar library event.
    static eventTemplate = "event.EventSlotCalendarCommonRenderer.event";

    setup() {
        super.setup(...arguments);
        useEffect(
            (fcEls) => {
                // Add overlay to disable days outside of event time range.
                const [rangeStartDate,] = this.props.model.meta.context.event_start_date.split(' ');
                const [rangeEndDate,] = this.props.model.meta.context.event_end_date.split(' ');
                for (const fcEl of fcEls) {
                    fcEl.querySelectorAll(".fc-day:not(.fc-col-header-cell)").forEach((dayEl) => {
                        if (dayEl.dataset.date < rangeStartDate || dayEl.dataset.date > rangeEndDate) {
                            dayEl.classList.add("bg-secondary", "bg-opacity-25", "pe-none");
                        }
                    });
                }
            },
            () => [[this.fc.el]],
        );
    }
}

export class EventSlotCalendarRenderer extends CalendarRenderer {
    static components = {
        ...CalendarRenderer.components,
        day: EventSlotCalendarCommonRenderer,
        week: EventSlotCalendarCommonRenderer,
        month: EventSlotCalendarCommonRenderer,
        year: CalendarYearRenderer,
    };
}
