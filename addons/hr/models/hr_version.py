# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class HrVersion(models.Model):
    _name = 'hr.version'
    _description = 'Version'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # TODO: remove later ? (see if still needed because contract template)
    _mail_post_access = 'read'
    _order = 'date_version'
    _rec_name = 'employee_id'

    def _get_default_address_id(self):
        address = self.env.user.company_id.partner_id.address_get(['default'])
        return address['default'] if address else False

    company_id = fields.Many2one(related='employee_id.company_id', readonly=False,
                                 store=True, default=lambda self: self.env.company)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        index=True)
    name = fields.Char()
    display_name = fields.Char(compute='_compute_display_name')
    active = fields.Boolean(default=True)

    date_version = fields.Date(required=True, default=fields.Date.today, tracking=True, groups="hr.group_hr_user")
    last_modified_uid = fields.Many2one('res.users', string='Last Modified by',
                                        default=lambda self: self.env.uid, required=True, groups="hr.group_hr_user")
    last_modified_date = fields.Datetime(string='Last Modified on', default=fields.Datetime.now, required=True,
                                         groups="hr.group_hr_user")

    # Personal Information
    country_id = fields.Many2one(
        'res.country', 'Nationality (Country)', groups="hr.group_hr_user", tracking=True)
    identification_id = fields.Char(string='Identification No', groups="hr.group_hr_user", tracking=True)
    ssnid = fields.Char('SSN No', help='Social Security Number', groups="hr.group_hr_user", tracking=True)
    passport_id = fields.Char('Passport No', groups="hr.group_hr_user", tracking=True)
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], groups="hr.group_hr_user", tracking=True, help="This is the legal sex recognized by the state.")

    private_street = fields.Char(string="Private Street", groups="hr.group_hr_user")
    private_street2 = fields.Char(string="Private Street2", groups="hr.group_hr_user")
    private_city = fields.Char(string="Private City", groups="hr.group_hr_user")
    private_state_id = fields.Many2one(
        "res.country.state", string="Private State",
        domain="[('country_id', '=?', private_country_id)]",
        groups="hr.group_hr_user")
    private_zip = fields.Char(string="Private Zip", groups="hr.group_hr_user")
    private_country_id = fields.Many2one("res.country", string="Private Country",
                                         groups="hr.group_hr_user")

    distance_home_work = fields.Integer(string="Home-Work Distance", groups="hr.group_hr_user", tracking=True)
    km_home_work = fields.Integer(string="Home-Work Distance in Km", groups="hr.group_hr_user",
                                  compute="_compute_km_home_work", inverse="_inverse_km_home_work", store=True)
    distance_home_work_unit = fields.Selection([
        ('kilometers', 'km'),
        ('miles', 'mi'),
    ], 'Home-Work Distance unit', groups="hr.group_hr_user", default='kilometers', required=True, tracking=True)

    marital = fields.Selection(
        selection='_get_marital_status_selection',
        string='Marital Status',
        groups="hr.group_hr_user",
        default='single',
        required=True,
        tracking=True)
    spouse_complete_name = fields.Char(string="Spouse Legal Name", groups="hr.group_hr_user", tracking=True)
    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="hr.group_hr_user", tracking=True)
    children = fields.Integer(string='Dependent Children', groups="hr.group_hr_user", tracking=True)

    # Work Information
    employee_type = fields.Selection([
            ('employee', 'Employee'),
            ('worker', 'Worker'),
            ('student', 'Student'),
            ('trainee', 'Trainee'),
            ('contractor', 'Contractor'),
            ('freelance', 'Freelancer'),
        ], string='Employee Type', default='employee', required=True, groups="hr.group_hr_user")
    department_id = fields.Many2one('hr.department', check_company=True, tracking=True)
    member_of_department = fields.Boolean("Member of department", compute='_compute_part_of_department', search='_search_part_of_department',
        help="Whether the employee is a member of the active user's department or one of it's child department.")
    job_id = fields.Many2one('hr.job', check_company=True, tracking=True)
    job_title = fields.Char(related='job_id.name', readonly=False, string="Job Title", groups="hr.group_hr_user")
    parent_id = fields.Many2one('hr.employee', 'Manager', compute="_compute_parent_id",
                                store=True, readonly=False, tracking=True,
                                domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids)]")
    coach_id = fields.Many2one(
        'hr.employee', 'Coach', compute='_compute_coach', store=True, readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids)]",
        help='Select the "Employee" who is the coach of this employee.\n'
             'The "Coach" has no specific rights or responsibilities by default.')

    address_id = fields.Many2one(
        'res.partner',
        string='Work Address',
        default=_get_default_address_id,
        store=True,
        readonly=False,
        check_company=True)
    work_location_id = fields.Many2one('hr.work.location', 'Work Location',
                                       domain="[('address_id', '=', address_id)]")
    work_location_name = fields.Char("Work Location Name", compute="_compute_work_location_name_type")
    work_location_type = fields.Selection([
        ("home", "Home"),
        ("office", "Office"),
        ("other", "Other")], compute="_compute_work_location_name_type", groups="hr.group_hr_user")

    departure_reason_id = fields.Many2one("hr.departure.reason", string="Departure Reason",
                                          groups="hr.group_hr_user", copy=False, ondelete='restrict', tracking=True)
    departure_description = fields.Html(string="Additional Information", groups="hr.group_hr_user", copy=False)
    departure_date = fields.Date(string="Departure Date", groups="hr.group_hr_user", copy=False, tracking=True)

    resource_calendar_id = fields.Many2one('resource.calendar', check_company=True, string="Working Hours", tracking=True)
    is_flexible = fields.Boolean(compute='_compute_is_flexible', store=True, groups="hr.group_hr_user")
    is_fully_flexible = fields.Boolean(compute='_compute_is_flexible', store=True, groups="hr.group_hr_user")
    tz = fields.Selection(
        _tz_get, string='Timezone', required=True,
        default=lambda self: self._context.get('tz') or self.env.user.tz or self.env.ref('base.user_admin').tz or 'UTC',
        help="This field is used in order to define in which timezone the employee will work.")

    # Contract Information
    contract_date_start = fields.Date('Contract Start Date', tracking=True, groups="hr.group_hr_user")
    contract_date_end = fields.Date(
        'Contract End Date', tracking=True, help="End date of the contract (if it's a fixed-term contract).",
        groups="hr.group_hr_user")
    trial_date_end = fields.Date('End of Trial Period', help="End date of the trial period (if there is one).",
                                 groups="hr.group_hr_user")
    date_start = fields.Date(compute='_compute_dates', groups="hr.group_hr_user")
    date_end = fields.Date(compute='_compute_dates', groups="hr.group_hr_user")
    is_current = fields.Boolean(compute='_compute_state', groups="hr.group_hr_user")
    is_past = fields.Boolean(compute='_compute_state', groups="hr.group_hr_user")
    is_future = fields.Boolean(compute='_compute_state', groups="hr.group_hr_user")
    is_in_contract = fields.Boolean(compute='_compute_state', groups="hr.group_hr_user")

    contract_template_id = fields.Many2one(
        'hr.version', string="Contract Template", groups="hr.group_hr_user",
        domain="[('company_id', '=', company_id), ('employee_id', '=', False)]",
        help="Select a contract template to auto-fill the contract form with predefined values. You can still edit the fields as needed after applying the template.")
    structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type",
                                        compute="_compute_structure_type_id", readonly=False, store=True, tracking=True,
                                        groups="hr.group_hr_user")
    active_employee = fields.Boolean(related="employee_id.active", string="Active Employee", groups="hr.group_hr_user")
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    wage = fields.Monetary('Wage', tracking=True, help="Employee's monthly gross wage.", aggregator="avg",
                           groups="hr.group_hr_user")
    contract_wage = fields.Monetary('Contract Wage', compute='_compute_contract_wage', groups="hr.group_hr_user")
    notes = fields.Html('Notes', groups="hr.group_hr_user")
    company_country_id = fields.Many2one('res.country', string="Company country",
                                         related='company_id.country_id', readonly=True)
    country_code = fields.Char(related='company_country_id.code', depends=['company_country_id'], readonly=True,
                               groups="hr.group_hr_user")
    contract_type_id = fields.Many2one('hr.contract.type', "Contract Type", tracking=True,
                                       groups="hr.group_hr_user")

    def _get_hr_responsible_domain(self):
        return "[('share', '=', False), ('company_ids', 'in', company_id), ('all_group_ids', 'in', %s)]" % self.env.ref('hr.group_hr_user').id

    hr_responsible_id = fields.Many2one(
        'res.users', 'HR Responsible', tracking=True,
        help='Person responsible for validating the employee\'s contracts.', domain=_get_hr_responsible_domain,
        default=lambda self: self.env.user, required=True, groups="hr.group_hr_user")

    @api.constrains('contract_date_start', 'contract_date_end')
    def _check_dates(self):
        for version in self:
            if version.contract_date_end and not version.contract_date_start:
                raise ValidationError(_('The contract must have a start date.'))
            elif version.contract_date_end and version.contract_date_start > version.contract_date_end:
                raise ValidationError(_(
                    'Start date (%(start)s) must be earlier than contract end date (%(end)s).',
                    start=version.contract_date_start, end=version.contract_date_end,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        versions = super().create(vals_list)
        for vals in vals_list:
            if 'contract_template_id' in vals:
                versions.copy_from_contract_template(self.env['hr.version'].browse(vals['contract_template_id']))
                versions.update(vals)
        return versions

    @api.ondelete(at_uninstall=False)
    def _unlink_except_last_version(self):
        if self.employee_id.versions_count == len(self):
            raise ValidationError(_('An employee must always have at least one version.'))

    @api.depends('date_version')
    def _compute_display_name(self):
        for version in self:
            version.display_name = version.name if not version.employee_id else date.strftime(version.date_version, '%-d %b %Y')

    def _compute_state(self):
        for version in self:
            version.is_current = version._is_current()
            version.is_past = version._is_past()
            version.is_future = version._is_future()
            version.is_in_contract = version._is_in_contract()

    def _is_current(self, date=fields.Date.today()):
        return self.date_start <= date and (not self.date_end or self.date_end >= date)

    def _is_past(self, date=fields.Date.today()):
        return self.date_end and self.date_end < date

    def _is_future(self, date=fields.Date.today()):
        return self.date_start > date

    def _is_in_contract(self, date=fields.Date.today()):
        # Return True if the employee is in contract on a given date
        return ((not self.contract_date_start or self.date_start <= date) and
                (not self.date_end or self.date_end >= date))

    def is_overlapping_period(self, date_from, date_to):
        """
        Return True if the employee is at least in contract one day during the period given
        :param date date_from: the start of the period
        :param date date_to: the stop of the period
        """
        return ((not self.contract_date_start or self.date_start <= date_to) and
            (not self.date_end or self.date_end >= date_from))

    def _is_fully_flexible(self):
        """ return True if the version has a fully flexible working calendar """
        self.ensure_one()
        return not self.resource_calendar_id

    @api.depends('resource_calendar_id.flexible_hours')
    def _compute_is_flexible(self):
        for version in self:
            version.is_fully_flexible = version._is_fully_flexible()
            version.is_flexible = version.is_fully_flexible or version.resource_calendar_id.flexible_hours

    @api.model
    def _get_whitelist_fields_from_template(self):
        # Add here any field that you want to copy from a contract template
        # Those fields should have tracking=True in hr.version to see the change
        return ['job_id', 'department_id', 'contract_type_id', 'structure_type_id', 'wage', 'resource_calendar_id']

    def copy_from_contract_template(self, contract_template_id):
        if not contract_template_id:
            return
        whitelist = self._get_whitelist_fields_from_template()
        for field in contract_template_id._fields:
            if field in whitelist and not self.env['hr.version']._fields[field].related:
                for version in self:
                    version[field] = contract_template_id[field]

    @api.depends('wage')
    def _compute_contract_wage(self):
        for version in self:
            version.contract_wage = version._get_contract_wage()

    def _get_contract_wage(self):
        if not self:
            return 0
        self.ensure_one()
        return self[self._get_contract_wage_field()]

    def _get_contract_wage_field(self):
        self.ensure_one()
        return 'wage'

    def _get_normalized_wage(self):
        """ This method is overridden in hr_payroll, as without that module, nothing allows to know
        there's no way to determine the employee's pay frequency.
        """
        wage = self._get_contract_wage()
        # without payroll installed, we suppose that the employee with a specific schedule has a monthly salary
        if self.resource_calendar_id:
            if not self.resource_calendar_id.hours_per_week:
                return 0
            return wage * 12 / 52 / self.resource_calendar_id.hours_per_week
        # without any calendar, the employee has a fully flexible schedule and is supposedly working on an hourly wage
        return wage

    def _get_valid_employee_for_user(self):
        user = self.env.user
        # retrieve the employee of the current active company for the user
        employee = user.employee_id
        if not employee:
            # search for all employees as superadmin to not get blocked by multi-company rules
            user_employees = user.employee_id.sudo().search([
                ('user_id', '=', user.id)
            ])
            # the default company employee is most likely the correct one, but fallback to the first if not available
            employee = user_employees.filtered(lambda r: r.company_id == user.company_id) or user_employees[:1]
        return employee

    @api.constrains('ssnid')
    def _check_ssnid(self):
        # By default, a Social Security Number is always valid, but each localization
        # may want to add its own constraints
        pass

    @api.depends_context('uid', 'company')
    @api.depends('department_id')
    def _compute_part_of_department(self):
        user_employee = self._get_valid_employee_for_user()
        active_department = user_employee.department_id
        if not active_department:
            self.member_of_department = False
        else:
            def get_all_children(department):
                children = department.child_ids
                if not children:
                    return self.env['hr.department']
                return children + get_all_children(children)

            child_departments = active_department + get_all_children(active_department)
            for version in self:
                version.member_of_department = version.department_id in child_departments

    def _search_part_of_department(self, operator, value):
        if operator != 'in':
            return NotImplemented

        user_employee = self._get_valid_employee_for_user()
        if not user_employee.department_id:
            return [('id', 'in', user_employee.ids)]
        return [('department_id', 'child_of', user_employee.department_id.ids)]

    @api.depends('company_id')
    def _compute_structure_type_id(self):

        default_structure_by_country = {}

        def _default_salary_structure(country_id):
            default_structure = default_structure_by_country.get(country_id)
            if default_structure is None:
                default_structure = default_structure_by_country[country_id] = (
                    self.env['hr.payroll.structure.type'].search([('country_id', '=', country_id)], limit=1)
                    or self.env['hr.payroll.structure.type'].search([('country_id', '=', False)], limit=1)
                )
            return default_structure

        for version in self:
            if not version.structure_type_id or (version.structure_type_id.country_id and version.structure_type_id.country_id != version.company_id.country_id):
                version.structure_type_id = _default_salary_structure(version.company_id.country_id.id)

    @api.depends("work_location_id.name", "work_location_id.location_type")
    def _compute_work_location_name_type(self):
        for version in self:
            version.work_location_name = version.work_location_id.name or None
            version.work_location_type = version.work_location_id.location_type or 'other'

    @api.depends('distance_home_work', 'distance_home_work_unit')
    def _compute_km_home_work(self):
        for version in self:
            version.km_home_work = version.distance_home_work * 1.609 if version.distance_home_work_unit == "miles" else version.distance_home_work

    def _inverse_km_home_work(self):
        for version in self:
            version.distance_home_work = version.km_home_work / 1.609 if version.distance_home_work_unit == "miles" else version.km_home_work

    @api.depends(
        'contract_date_start', 'contract_date_end', 'date_version', 'employee_id',
        'employee_id.version_ids.date_version')
    def _compute_dates(self):
        for version in self:
            version.date_start = max(version.date_version, version.contract_date_start) \
                if version.contract_date_start \
                else version.date_version

            next_version = self.env['hr.version'].search([
                ('employee_id', '=', version.employee_id.id),
                ('date_version', '>', version.date_version)], limit=1)
            date_version_end = next_version.date_version + relativedelta(days=-1) if next_version else False

            if date_version_end and version.contract_date_end:
                version.date_end = min(date_version_end, version.contract_date_end)
            elif date_version_end:
                version.date_end = date_version_end
            else:
                version.date_end = version.contract_date_end

    @api.model
    def _get_marital_status_selection(self):
        return [
            ('single', _('Single')),
            ('married', _('Married')),
            ('cohabitant', _('Legal Cohabitant')),
            ('widower', _('Widower')),
            ('divorced', _('Divorced')),
        ]

    @api.depends('department_id')
    def _compute_parent_id(self):
        for version in self.filtered('department_id.manager_id'):
            version.parent_id = version.department_id.manager_id

    @api.depends('parent_id')
    def _compute_coach(self):
        for version in self:
            manager = version.parent_id
            previous_manager = version._origin.parent_id
            if manager and (version.coach_id == previous_manager or not version.coach_id):
                version.coach_id = manager
            elif not version.coach_id:
                version.coach_id = False

    def _get_salary_costs_factor(self):
        self.ensure_one()
        return 12.0

    def _is_struct_from_country(self, country_code):
        self.ensure_one()
        self_sudo = self.sudo()
        return self_sudo.structure_type_id and self_sudo.structure_type_id.country_id.code == country_code
