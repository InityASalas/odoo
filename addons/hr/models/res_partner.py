# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.tools.discuss import Store


class ResPartner(models.Model):
    _inherit = 'res.partner'

    employee_ids = fields.One2many(
        'hr.employee', 'work_contact_id', string='Employees', groups="hr.group_hr_user",
        help="Related employees based on their private address")
    employees_count = fields.Integer(compute='_compute_employees_count', groups="hr.group_hr_user")
    employee = fields.Boolean(help="Whether this contact is an Employee.", compute='_compute_employee', store=True, readonly=False)

    def _compute_employees_count(self):
        for partner in self:
            partner.employees_count = len(partner.sudo().employee_ids.filtered(lambda e: e.company_id in self.env.companies))

    def action_open_employees(self):
        self.ensure_one()
        if self.employees_count > 1:
            return {
                'name': _('Related Employees'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.employee',
                'view_mode': 'kanban',
                'domain': [('id', 'in', self.employee_ids.ids),
                           ('company_id', 'in', self.env.companies.ids)],
            }
        return {
            'name': _('Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self.employee_ids.filtered(lambda e: e.company_id in self.env.companies).id,
            'view_mode': 'form',
        }

    def _get_all_addr(self):
        self.ensure_one()
        employee_id = self.env['hr.employee'].search(
            [('id', 'in', self.employee_ids.ids)],
            limit=1,
        )
        if not employee_id:
            return super()._get_all_addr()

        pstl_addr = {
            'contact_type': 'employee',
            'street': employee_id.private_street,
            'zip': employee_id.private_zip,
            'city': employee_id.private_city,
            'country': employee_id.private_country_id.code,
        }
        return [pstl_addr] + super()._get_all_addr()

    @api.depends('employee_ids')
    def _compute_employee(self):
        employee_data = self.env['hr.employee']._read_group(
            domain=[('work_contact_id', 'in', self.ids)],
            groupby=['work_contact_id'],
        )
        employees = {employee for [employee] in employee_data}
        for partner in self:
            partner.employee = partner in employees

    def _get_avatar_store_fields(self):
        return super()._get_avatar_store_fields() + ["all_companies_employee_ids", "employee_ids"]

    def _get_avatar_employee_store_fields(self):
        return [
            "work_phone", "work_email", "work_location_name", "work_location_type",
            "job_title", Store.One("department_id", ["name"], sudo=True),
        ]

    def _to_store(self, store: Store, fields, *, main_user_by_partner=None):
        super()._to_store(
            store,
            [field for field in fields if field not in ["all_companies_employee_ids"]],
            main_user_by_partner=main_user_by_partner,
        )
        for partner in self:
            if "user" in fields:
                if "all_companies_employee_ids" in fields:
                    store.add(
                        partner,
                        {
                            "all_companies_employee_ids": Store.Many(
                                partner.mapped("user_ids.all_companies_employee_ids"),
                                self._get_avatar_employee_store_fields()
                            )
                        }
                    )
                if "employee_ids" in fields:
                    store.add(
                        partner,
                        {
                            "employee_ids": Store.Many(
                                partner.mapped("user_ids.employee_ids"),
                                self._get_avatar_employee_store_fields()
                            )
                        }
                    )
