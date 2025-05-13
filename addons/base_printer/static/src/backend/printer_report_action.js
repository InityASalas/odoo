import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

async function printerReportActionHandler(action, options, env) {
    if (action.printer_address) {
        const orm = env.services.orm;
        await orm.call("ir.actions.report", "render_and_send_email", [
            action.id,
            action.context.active_ids,
            action.data,
        ]);
        env.services.notification.add(_t("Email is sent to printer with attachment.."), {
            type: "info",
        });
        return { reportHandler: true, close_on_report_handler: true };
    }
}

registry
    .category("ir.actions.report handlers")
    .add("printer_report_action_handler", printerReportActionHandler);
