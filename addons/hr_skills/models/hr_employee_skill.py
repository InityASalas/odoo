# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import Domain

from collections import defaultdict


class HrEmployeeSkill(models.Model):
    _name = 'hr.employee.skill'
    _description = "Skill level for an employee"
    _order = "skill_type_id, skill_level_id"
    _rec_name = "skill_id"

    employee_id = fields.Many2one('hr.employee', required=True, index=True, ondelete='cascade')
    skill_id = fields.Many2one('hr.skill', compute='_compute_skill_id', store=True, domain="[('skill_type_id', '=', skill_type_id)]", readonly=False, required=True, ondelete='cascade')
    skill_level_id = fields.Many2one('hr.skill.level', compute='_compute_skill_level_id', domain="[('skill_type_id', '=', skill_type_id)]", store=True, readonly=False, required=True, ondelete='cascade')
    skill_type_id = fields.Many2one('hr.skill.type',
                                    default=lambda self: self.env['hr.skill.type'].search([], limit=1),
                                    required=True, ondelete='cascade')
    level_progress = fields.Integer(related='skill_level_id.level_progress')
    color = fields.Integer(related="skill_type_id.color")
    start_date = fields.Date(string="Validity Start", default=fields.Date.today())
    stop_date = fields.Date(string="Validity Stop")
    number_of_levels = fields.Integer(related="skill_type_id.number_of_levels")
    is_certification = fields.Boolean(related="skill_type_id.is_certification")
    display_warning = fields.Boolean()

    @api.constrains('start_date', 'stop_date')
    def _check_date(self):
        for record in self:
            if record.stop_date and record.start_date > record.stop_date:
                raise ValidationError(_("The stop date can't be earlier than the start date"))

    @api.constrains('skill_id', 'skill_type_id')
    def _check_skill_type(self):
        for record in self:
            if record.skill_id not in record.skill_type_id.skill_ids:
                raise ValidationError(_("The skill %(name)s and skill type %(type)s doesn't match", name=record.skill_id.name, type=record.skill_type_id.name))

    @api.constrains('skill_type_id', 'skill_level_id')
    def _check_skill_level(self):
        for record in self:
            if record.skill_level_id not in record.skill_type_id.skill_level_ids:
                raise ValidationError(_("The skill level %(level)s is not valid for skill type: %(type)s", level=record.skill_level_id.name, type=record.skill_type_id.name))

    @api.depends('skill_type_id')
    def _compute_skill_id(self):
        for record in self:
            if record.skill_type_id:
                record.skill_id = record.skill_type_id.skill_ids[0] if record.skill_type_id.skill_ids else False
            else:
                record.skill_id = False

    @api.depends('skill_id')
    def _compute_skill_level_id(self):
        for record in self:
            if not record.skill_id:
                record.skill_level_id = False
            else:
                if not record.skill_level_id:
                    skill_levels = record.skill_type_id.skill_level_ids
                    record.skill_level_id = skill_levels.filtered('default_level') or skill_levels[0] if skill_levels else False

    @api.depends('skill_id', 'skill_level_id')
    def _compute_display_name(self):
        for employee_skill in self:
            employee_skill.display_name = f"{employee_skill.skill_id.name}: {employee_skill.skill_level_id.name}"

    def _create_logs(self):
        today = fields.Date.context_today(self)
        employee_skills = self.env['hr.employee.skill'].search([
            ('employee_id', 'in', self.employee_id.ids)
        ])
        employee_skill_logs = self.env['hr.employee.skill.log'].search([
            ('employee_id', 'in', self.employee_id.ids),
        ])

        skills_by_employees = defaultdict(lambda: self.env['hr.employee.skill'])
        for skill in employee_skills:
            skills_by_employees[skill.employee_id.id] |= skill

        logs_by_employees = defaultdict(lambda: self.env['hr.employee.skill.log'])
        for log in employee_skill_logs:
            logs_by_employees[log.employee_id.id] |= log

        skill_to_create_vals = []
        for employee in skills_by_employees:
            employee_logs = logs_by_employees[employee]
            for employee_skill in skills_by_employees[employee]:
                existing_log = employee_logs.filtered(lambda l: l.department_id == employee_skill.employee_id.department_id and l.skill_id == employee_skill.skill_id and l.date == today)
                if existing_log:
                    existing_log.write({'skill_level_id': employee_skill.skill_level_id.id})
                else:
                    skill_to_create_vals.append({
                        'employee_id': employee_skill.employee_id.id,
                        'skill_id': employee_skill.skill_id.id,
                        'skill_level_id': employee_skill.skill_level_id.id,
                        'department_id': employee_skill.employee_id.department_id.id,
                        'skill_type_id': employee_skill.skill_type_id.id,
                    })

        if skill_to_create_vals:
            self.env['hr.employee.skill.log'].create(skill_to_create_vals)

    def _prepare_create_vals(self, vals_list):
        vals_to_return = []
        for vals in vals_list:
            employee_id = vals.get('employee_id', False)
            skill_id = vals.get('skill_id', False)
            skill_type_id = vals.get('skill_type_id', False)
            skill_level_id = vals.get('skill_level_id', False)

            employee_skill_already_exist = self.env['hr.employee.skill'].search([
                ('employee_id', '=', employee_id),
                ('skill_id', '=', skill_id),
                ('display_warning', '=', False),
            ])
            if employee_skill_already_exist:
                skill_type = self.env['hr.skill.type'].browse(skill_type_id)
                if not skill_type.is_certification:
                    # Only one employee skill per skill no certificate
                    employee_skill_already_exist[0].with_context(without_check=True).write({'skill_level_id': skill_level_id})
                else:
                    start_date = vals.get('start_date', False)
                    stop_date = vals.get('stop_date', False)
                    if not any(
                        employee_skill.start_date == start_date and employee_skill.stop_date == stop_date
                        for employee_skill in employee_skill_already_exist):
                        vals_to_return.append(vals)
            else:
                vals_to_return.append(vals)
        return vals_to_return

    def _prepare_update_vals(self, vals):
        to_remove = self.env['hr.employee.skill']

        for employee_skill in self:
            employee_id = vals.get('employee_id', employee_skill.employee_id.id)
            skill = self.env['hr.skill'].browse(vals['skill_id']) if 'skill_id' in vals else employee_skill.skill_id
            domain = Domain([
                ('employee_id', '=', employee_id),
                ('skill_id', '=', skill.id),
                ('display_warning', '=', False),
            ])

            if skill.skill_type_id.is_certification:
                start_date = vals.get('start_date', employee_skill.start_date)
                stop_date = vals.get('stop_date', employee_skill.stop_date)
                domain = Domain.AND([
                    [
                        ('start_date', '=', start_date),
                        ('stop_date', '=', stop_date),
                    ],
                domain])

            to_remove += self.env['hr.employee.skill'].search(domain)
        to_remove.unlink()

    def _trigger_conflict(self):
        employee_skill_by_employee_and_skill = self.grouped(
            lambda employee_skill: (employee_skill.employee_id, employee_skill.skill_id)
        )
        records_with_warning = self.env['hr.employee.skill']
        for employee_skills in employee_skill_by_employee_and_skill.values():
            if len(employee_skills) == 1:
                continue
            records_with_warning += employee_skills
        records_with_warning.with_context(without_log=True).write({'display_warning': True})

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = self._prepare_create_vals(vals_list)
        if new_vals_list:
            employee_skills = super().create(new_vals_list)
            employee_skills._create_logs()
            return employee_skills
        return self.env['hr.employee.skill']

    def write(self, vals):
        conflicting_fields = ['employee_id', 'skill_id', 'skill_level_id', 'start_date', 'stop_date']
        if not self.env.context.get('without_check', False) and any(field in vals for field in conflicting_fields):
            self._prepare_update_vals(vals)
        res = super().write(vals)
        if not self.env.context.get('without_log', False):
            self._create_logs()
        return res
