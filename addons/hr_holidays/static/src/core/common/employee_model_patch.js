import { patch } from "@web/core/utils/patch";
import { fields } from "@mail/model/misc";
import { Employee } from "@hr/core/common/employee_model";

patch(Employee.prototype, {
    leave_date_to: fields.Datetime(),
});
