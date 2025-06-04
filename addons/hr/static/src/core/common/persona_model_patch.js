import { Persona } from "@mail/core/common/persona_model";
import { fields } from "@mail/core/common/record";

import { patch } from "@web/core/utils/patch";

patch(Persona.prototype, {
    setup() {
        super.setup();
        /** @type {number|undefined} */
        this.employee_ids = fields.Many("hr.employee");
        this.all_companies_employee_ids = fields.Many("hr.employee");
    },
});
