from datetime import date, timedelta

from odoo import Command
from odoo.tests import HttpCase, tagged, users


@tagged("post_install", "-at_install")
class TestAvatarCardTour(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company_2 = (
            cls.env["res.company"]
            .sudo()
            .create(
                {
                    "name": "Test Company Avatar Card Tour",
                    "country_id": cls.env.ref("base.be").id,
                }
            )
        )
        leave_type = (
            cls.env["hr.leave.type"]
            .with_company(company_2)
            .sudo()
            .create(
                {
                    "name": "Time Off multi company",
                    "company_id": company_2.id,
                    "time_type": "leave",
                    "requires_allocation": False,
                }
            )
        )
        cls.test_user = (
            cls.env["res.users"]
            .with_company(company_2)
            .sudo()
            .create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "password": "test_password",
                    "company_id": company_2.id,
                    "company_ids": [(6, 0, [company_2.id])],
                    "partner_id": cls.env["res.partner"]
                    .create(
                        {
                            "name": "Test User Partner",
                            "company_id": company_2.id,
                            "email": "test@test.com",
                            "phone": "123456789",
                        }
                    )
                    .id,
                }
            )
        )

        cls.test_user.partner_id.write(
            {
                "user_id": cls.test_user.id,
            }
        )
        test_employee = (
            cls.env["hr.employee"]
            .with_company(company_2)
            .sudo()
            .create(
                {
                    "name": "Test Employee",
                    "user_id": cls.test_user.id,
                    "company_id": company_2.id,
                    "department_id": cls.env["hr.department"]
                    .with_company(company_2)
                    .sudo()
                    .create(
                        {
                            "name": "Test Department",
                            "company_id": company_2.id,
                        }
                    )
                    .id,
                    "job_title": "Test Job Title",
                    "work_phone": "987654321",
                    "work_email": "test_employee@test.com",
                }
            )
        )
        cls.env["hr.leave"].with_company(company_2).sudo().with_context(
            leave_skip_state_check=True
        ).create(
            {
                "name": "Test Leave",
                "company_id": company_2.id,
                "holiday_status_id": leave_type.id,
                "employee_id": test_employee.id,
                "request_date_from": (date.today() - timedelta(days=1)),
                "request_date_to": (date.today() + timedelta(days=1)),
                "state": "validate",
            }
        )

    @users("admin", "demo")
    def test_avatar_card_tour_multi_company(self):
        channel = (
            self.env["discuss.channel"]
            .sudo()
            .create(
                {
                    "name": "Test Chat",
                    "channel_type": "chat",
                    "channel_member_ids": [
                        Command.create(
                            {
                                "partner_id": self.test_user.partner_id.id,
                            }
                        ),
                        Command.create(
                            {
                                "partner_id": self.env.user.partner_id.id,
                            }
                        ),
                    ],
                }
            )
        )
        channel.with_user(self.test_user).message_post(
            body="Test message in chat",
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        self.start_tour("/", "avatar_card_tour", login=self.env.user.login)
