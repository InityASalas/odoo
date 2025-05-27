# Part of Odoo. See LICENSE file for full copyright and licensing details.

import warnings
import pytz
from datetime import datetime, time

from odoo import models
from odoo.tools.date_utils import convert_timezone

warnings.filterwarnings("ignore", category=DeprecationWarning)
import holidays  # noqa: E402


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _generate_public_holidays(self, year_range, convert_datetime=True):
        response = []
        subdivision_per_country_dict = holidays.list_supported_countries(include_aliases=True)
        lang_per_country = holidays.list_localized_countries(include_aliases=True)
        existing_holidays_dict = dict(self.env["resource.calendar.leaves"]._read_group(
            domain=[
                ('company_id', 'in', self.ids),
                ('date_from', '>=', datetime(year_range[0] - 1, 12, 31, 0, 0, 0)),
                ('date_to', '<=', datetime(year_range[-1] + 1, 1, 2, 0, 0, 0)),
                ('resource_id', '=', False),
            ],
            groupby=['company_id'],
            aggregates=['id:recordset'],
        ))

        for company in self:
            if not company.country_code:
                response.append({
                    'title': self.env._('No Country Code'),
                    'type': 'danger',
                    'message': self.env._('Please select a country in %(company)s to load public holidays.', company=company.name),
                })
                continue
            if company.country_code not in subdivision_per_country_dict:
                response.append({
                    'title': self.env._('No Public Holidays'),
                    'type': 'danger',
                    'message': self.env._('Public holidays are not available for %(country)s country.', country=company.country_id.name),
                })
                continue

            company_subdiv = company.state_id.code
            subdiv = subdivision_per_country_dict.get(company.country_code, None)
            user_lang_iso_code = self.env["res.lang"]._lang_get(self.env.user.lang).iso_code[:2]
            if not user_lang_iso_code or user_lang_iso_code not in lang_per_country.get(company.country_code, []):
                user_lang_iso_code = 'en_US'

            public_holiday_dict = holidays.country_holidays(
                company.country_code,
                subdiv=company_subdiv if subdiv and company_subdiv in subdiv else None,
                years=year_range,
                language=user_lang_iso_code,
            )

            overlapped_holidays = False
            company_tz = pytz.timezone(company.resource_calendar_id.tz)
            public_holidays_values_dict = {}

            for holiday_date, holiday_name in public_holiday_dict.items():
                holiday_start_utc = convert_timezone(datetime.combine(holiday_date, time.min), pytz.utc, company_tz)
                holiday_end_utc = convert_timezone(datetime.combine(holiday_date, time.max), pytz.utc, company_tz)
                overlapping = any(
                    holiday.date_from <= holiday_end_utc and
                    holiday.date_to >= holiday_start_utc
                    for holiday in existing_holidays_dict.get(company, [])
                )
                if overlapping:
                    overlapped_holidays = True
                    continue
                if holiday_date in public_holidays_values_dict:
                    public_holidays_values_dict[holiday_date]['name'] += f" / {holiday_name}"
                else:
                    public_holidays_values_dict[holiday_date] = {
                        'name': holiday_name,
                        'date_from': holiday_start_utc,
                        'date_to': holiday_end_utc,
                        'company_id': company.id,
                    }

            new_public_holidays = self.env['resource.calendar.leaves'].with_context(convert_datetime=convert_datetime).create(
                list(public_holidays_values_dict.values()),
            )
            notification = {
                'title': self.env._('Public Holidays Import Notification'),
                'type': 'success',
                'message': self.env._('No new public time off were added as they already exist.'),
            }
            if not new_public_holidays:
                response.append(notification)
            else:
                notification['message'] = self.env._(
                    "Public holidays have been successfully created for %(company)s for the next %(years)s years.",
                    company=company.name, years=len(year_range))
                if overlapped_holidays:
                    notification['message'] += " " + self.env._("Some were overlapping existing ones, not all records have been created.")
                response.append(notification)

        return response

    def load_public_holidays(self, convert_datetime=True):
        warnings = []
        if not self:
            warnings.append({
                'title': self.env._('No Company'),
                'type': 'danger',
                'message': self.env._('Please select a company to load public holidays.'),
            })
        else:
            current_year = datetime.now().year
            warnings.extend(self._generate_public_holidays(
                year_range=range(current_year, current_year + 5),
                convert_datetime=convert_datetime,
            ))
        for warning in warnings:
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification',
                warning,
            )

    def _cron_load_current_year_public_holidays(self):
        current_year = datetime.now().year
        self.env.companies._generate_public_holidays(
            year_range=[current_year, current_year + 1],
            convert_datetime=False,
        )
