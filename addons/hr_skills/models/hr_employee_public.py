# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    resume_line_ids = fields.One2many('hr.resume.line', 'employee_id', string="Resume lines")
    employee_skill_ids = fields.One2many('hr.employee.skill', 'employee_id', string="Skills",
        domain=[('skill_type_id.active', '=', True)])
    current_employee_skill_ids = fields.One2many('hr.employee.skill',
        compute='_compute_current_employee_skill_ids', readonly=False)
    certification_ids = fields.One2many('hr.employee.skill', related="employee_id.certification_ids")

    @api.depends('employee_skill_ids')
    def _compute_current_employee_skill_ids(self):
        for employee in self:
            employee.current_employee_skill_ids = employee.employee_skill_ids.filtered(
                lambda employee_skill: employee_skill.is_certification or
                    not employee_skill.valid_to or employee_skill.valid_to >= fields.Date.today()
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "current_employee_skill_ids" in vals:
                vals['employee_skill_ids'] = vals.pop('current_employee_skill_ids')
        return super().create(vals_list)

    def write(self, vals):
        if "current_employee_skill_ids" in vals:
            vals['employee_skill_ids'] = vals.pop("current_employee_skill_ids")
        res = super().write(vals)
        return res
