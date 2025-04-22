# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

from odoo.tests import Form
from odoo.tests.common import TransactionCase, new_test_user


class TestResourceSkills(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_hr = new_test_user(cls.env, login='hr', groups='hr.group_hr_user')
        cls.emp1, cls.emp2, cls.emp3 = cls.env['hr.employee'].create([
            {'name': 'emp1'},
            {'name': 'emp2'},
            {'name': 'emp3'},
        ])

        cls.skill_type_without_certificate, cls.skill_type_with_certificate = cls._create_skill_types([
            {
                'name': "without certificate",
                'number_of_skills': 3,
                'number_of_levels': 3,
            }, {
                'name': "with certificate",
                'number_of_skills': 3,
                'number_of_levels': 3,
                'certificate': True,
            },
        ])

# |----------------------------------------------------|  |------------------------------------------------------|
# |                       Skills                       |  |                          Level                       |
# |----------------------------------------------------|  |------------------------------------------------------|
# | Id  |  Skill Type  |              Name             |  |   Id  |  Skill Type  |              Name             |
# |   1 |            1 |  Skill 1 without certificate  |  |     1 |            1 |   level 1 without certificate |
# |   2 |            1 |  Skill 2 without certificate  |  |     2 |            1 |   level 2 without certificate |
# |   3 |            1 |  Skill 3 without certificate  |  |     3 |            1 |   level 3 without certificate |
# |   4 |            2 |     Skill 1 with certificate  |  |     4 |            2 |      level 1 with certificate |
# |   5 |            2 |     Skill 2 with certificate  |  |     5 |            2 |      level 2 with certificate |
# |   6 |            2 |     Skill 3 with certificate  |  |     6 |            2 |      level 3 with certificate |
# |----------------------------------------------------|  |------------------------------------------------------|

# |---------------------------------------------------------------------------------------------------------|
# |                                              Employee Skill                                             |
# |---------------------------------------------------------------------------------------------------------|
# |  Id  |  Skill Type  |  Skill  |  Level  |  Employee (name)  | Certificate  |  Start Date  |  Stop Date  |
# |    1 |            2 |       4 |      4  |             emp1  |        True  |     23-02-01 |   24-02-01  |
# |    2 |            2 |       5 |      4  |             emp1  |        True  |     23-02-01 |   24-02-01  |
# |    3 |            1 |       1 |      1  |             emp1  |       False  |            - |           - |
# |    4 |            1 |       1 |      2  |             emp2  |       False  |            - |           - |
# |    5 |            1 |       2 |      2  |             emp1  |       False  |            - |           - |
# |    6 |            1 |       3 |      1  |             emp1  |       False  |            - |           - |
# |---------------------------------------------------------------------------------------------------------|

        cls.line1, cls.line2, cls.line3, cls.line4, cls.line5, cls.line6 = cls.env['hr.employee.skill'].create([
            {
                'skill_type_id': cls.skill_type_with_certificate.id,
                'skill_id': cls.skill_type_with_certificate.skill_ids[0].id,
                'skill_level_id': cls.skill_type_with_certificate.skill_level_ids[0].id,
                'employee_id': cls.emp1.id,
                'start_date': datetime.date(2023, 2, 1),
                'stop_date': datetime.date(2024, 2, 1),
            }, {
                'skill_type_id': cls.skill_type_with_certificate.id,
                'skill_id': cls.skill_type_with_certificate.skill_ids[1].id,
                'skill_level_id': cls.skill_type_with_certificate.skill_level_ids[0].id,
                'employee_id': cls.emp1.id,
                'start_date': datetime.date(2023, 2, 1),
                'stop_date': datetime.date(2024, 2, 1),
            }, {
                'skill_type_id': cls.skill_type_without_certificate.id,
                'skill_id': cls.skill_type_without_certificate.skill_ids[0].id,
                'skill_level_id': cls.skill_type_without_certificate.skill_level_ids[0].id,
                'employee_id': cls.emp1.id,
            }, {
                'skill_type_id': cls.skill_type_without_certificate.id,
                'skill_id': cls.skill_type_without_certificate.skill_ids[0].id,
                'skill_level_id': cls.skill_type_without_certificate.skill_level_ids[1].id,
                'employee_id': cls.emp2.id,
            }, {
                'skill_type_id': cls.skill_type_without_certificate.id,
                'skill_id': cls.skill_type_without_certificate.skill_ids[1].id,
                'skill_level_id': cls.skill_type_without_certificate.skill_level_ids[1].id,
                'employee_id': cls.emp1.id,
            }, {
                'skill_type_id': cls.skill_type_without_certificate.id,
                'skill_id': cls.skill_type_without_certificate.skill_ids[2].id,
                'skill_level_id': cls.skill_type_without_certificate.skill_level_ids[0].id,
                'employee_id': cls.emp1.id,
            },
        ])

    @classmethod
    def _create_skill_types(self, vals_list):
        skill_types = self.env['hr.skill.type']
        for vals in vals_list:
            with Form(self.env['hr.skill.type']) as skill_type_form:
                skill_type_form.name = vals['name']
                skill_type_form.is_certification = vals.get('certificate', False)
                for i in range(vals['number_of_skills']):
                    with skill_type_form.skill_ids.new() as skill:
                        skill.name = f"Skill {i} {vals['name']}"
                for x in range(vals['number_of_levels']):
                    with skill_type_form.skill_level_ids.new() as level:
                        level.name = f"level {x} {vals['name']}"
                        level.level_progress = x * vals['number_of_levels']
            skill_types += skill_type_form.save()
        return skill_types

    def test_write_certificate_skill_1(self):
        # line1 and line2 will be equal; line2 will be updated and line 1 will be removed
        self.line2.write({'skill_id': self.skill_type_with_certificate.skill_ids[0].id})
        self.assertEqual(self.env['hr.employee.skill'].search_count([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_with_certificate.skill_ids[0].id)
        ]), 1)

    def test_write_certificate_skill_2(self):
        # line2 will be updated
        self.line2.write({
            'skill_id': self.skill_type_with_certificate.skill_ids[0].id,
            'start_date': datetime.date(2023, 1, 1),
        })
        self.assertEqual(self.env['hr.employee.skill'].search_count([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_with_certificate.skill_ids[0].id)
        ]), 2)

    def test_write_without_certificate_skill_1(self):
        # The employee skill's with id = 6 will be deleted because employee 1 will have two employee skill
        # (not certification) with the same skill; so only the earliest will be kept.
        self.line5.write({'skill_id': self.skill_type_without_certificate.skill_ids[2].id})
        employee_skill = self.env['hr.employee.skill'].search([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_without_certificate.skill_ids[2].id)
        ])
        self.assertEqual(len(employee_skill.ids), 1)
        self.assertEqual(employee_skill.skill_level_id.id, self.skill_type_without_certificate.skill_level_ids[1].id)

    def test_write_without_certificate_skill_2(self):
        # The employee skill's with id = 3 will be deleted because employee 1 will have two employee skill
        # (no certification) with the same skill; so only the earliest will be kept.
        self.line4.write({'employee_id': self.emp1.id})
        employee_skill = self.env['hr.employee.skill'].search([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_without_certificate.skill_ids[0].id)
        ])
        self.assertEqual(len(employee_skill.ids), 1)
        self.assertEqual(employee_skill.skill_level_id.id, self.skill_type_without_certificate.skill_level_ids[1].id)

    def test_create_with_certificate_skill_check_start_date(self):
        # For employee skill with certification, a record will not be created only with the exact employee skill exist.
        # The start/stop date needs to be the same.

        # Same date_from as line 1 but without stop_date
        self.env['hr.employee.skill'].create({
            'skill_type_id': self.skill_type_with_certificate.id,
            'skill_id': self.skill_type_with_certificate.skill_ids[0].id,
            'skill_level_id': self.skill_type_with_certificate.skill_level_ids[0].id,
            'employee_id': self.emp1.id,
            'start_date': datetime.date(2023, 2, 1),
            'stop_date': False,
        })

        # This employee skill is included in line 1
        self.env['hr.employee.skill'].create({
            'skill_type_id': self.skill_type_with_certificate.id,
            'skill_id': self.skill_type_with_certificate.skill_ids[0].id,
            'skill_level_id': self.skill_type_with_certificate.skill_level_ids[0].id,
            'employee_id': self.emp1.id,
            'start_date': datetime.date(2023, 3, 1),
            'stop_date': datetime.date(2024, 1, 1),
        })

        # The same as line 1, so should not be created
        self.env['hr.employee.skill'].create({
            'skill_type_id': self.skill_type_with_certificate.id,
            'skill_id': self.skill_type_with_certificate.skill_ids[0].id,
            'skill_level_id': self.skill_type_with_certificate.skill_level_ids[0].id,
            'employee_id': self.emp1.id,
            'start_date': datetime.date(2023, 2, 1),
            'stop_date': datetime.date(2024, 2, 1),
        })

        self.assertEqual(self.env['hr.employee.skill'].search_count([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_with_certificate.skill_ids[0].id),
            ('skill_level_id', '=', self.skill_type_with_certificate.skill_level_ids[0].id),
        ]), 3)

    def test_create_with_certificate_skill_allow_double_level(self):
        self.env['hr.employee.skill'].create({
            'skill_type_id': self.skill_type_with_certificate.id,
            'skill_id': self.skill_type_with_certificate.skill_ids[1].id,
            'skill_level_id': self.skill_type_with_certificate.skill_level_ids[1].id,
            'employee_id': self.emp1.id,
            'start_date': datetime.date(2024, 2, 1),
            'stop_date': datetime.date(2025, 2, 1),
        })

        self.assertEqual(self.env['hr.employee.skill'].search_count([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_with_certificate.skill_ids[1].id),
        ]), 2)

    def test_create_without_certificate_skill_replace_level(self):
        # Employee 1 already have this employee skill with an other level, so the level should be updated and this
        # record should not be created.

        self.env['hr.employee.skill'].create({
            'skill_type_id': self.skill_type_without_certificate.id,
            'skill_id': self.skill_type_without_certificate.skill_ids[2].id,
            'skill_level_id': self.skill_type_without_certificate.skill_level_ids[2].id,
            'employee_id': self.emp1.id,
        })

        employee_skills = self.env['hr.employee.skill'].search([
            ('employee_id', '=', self.emp1.id),
            ('skill_id', '=', self.skill_type_without_certificate.skill_ids[2].id),
        ])
        self.assertEqual(len(employee_skills.ids), 1)
        self.assertEqual(employee_skills.skill_level_id.id, self.skill_type_without_certificate.skill_level_ids[2].id)
