import { Record } from "@mail/core/common/record";

export class Department extends Record {
    static _name = "hr.department";
    static id = "id";

    /** @type {number} */
    id;

    /** @type {string} */
    name;
}

Department.register();
