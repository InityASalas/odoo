# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.hr_work_entry.tests.common import TestWorkEntryBase
from odoo.addons.hr_holidays.tests.common import TestHolidayContract
from odoo.fields import Datetime

class TestWorkEntryHolidaysBase(TestWorkEntryBase, TestHolidayContract):

    @classmethod
    def setUpClass(cls):
        super(TestWorkEntryHolidaysBase, cls).setUpClass()
        cls.leave_type.work_entry_type_id = cls.work_entry_type_leave.id

    @classmethod
    def create_leave(cls, date_from=None, date_to=None, name="", employee_id=False):
        return cls.env['hr.leave'].create({
            'name': name or 'Holiday!!!',
            'employee_id': employee_id or cls.richard_emp.id,
            'holiday_status_id': cls.leave_type.id,
            'request_date_to': date_to or Datetime.today(),
            'request_date_from': date_from or Datetime.today(),
        })
