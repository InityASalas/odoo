# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployeeSkill(models.Model):
    _name = 'hr.employee.skill'
    _inherit = 'hr.individual.skill.mixin'
    _description = "Skill level for employee"
    _order = "skill_type_id, skill_level_id"
    _rec_name = "skill_id"
    _linked_field_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', required=True, index=True, ondelete='cascade')
