import { Record, fields } from "@mail/core/common/record";

export class Employee extends Record {
    static _name = "hr.employee";
    static id = "id";

    /** @type {number} */
    id;

    /** @type {string} */
    work_phone;
    /** @type {string} */
    work_email;
    /** @type {string} */
    work_location_type;
    /** @type {string} */
    work_location_name;
    /** @type {string} */
    job_title;
    department_id = fields.One("hr.department");
}

Employee.register();
