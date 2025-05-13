# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    printer_address = fields.Char(string="Printer Address", help="Enter the IP address or email address of the printer to send print jobs directly to the configured printer.")

    def render_and_send_email(self, active_record_ids, data):
        """
        Generate a PDF report and send it via email to the configured printer address
        """
        self.ensure_one()
        datas = self._render(self.report_name, active_record_ids, data)
        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(datas[0]),
            'mimetype': 'application/pdf',
        })

        mail_template = self.env.ref('base_printer.mail_template_print_attachment', raise_if_not_found=False)
        if not mail_template:
            raise UserError(_("The mail template with XML ID '%s' was not found.", 'base_printer.mail_template_print_attachment'))

        mail_template.send_mail(self.id, force_send=True, email_values={'email_to': self.printer_address, 'attachment_ids': attachment.ids})

    def report_action(self, docids, data=None, config=True):
        result = super().report_action(docids, data, config)
        if result.get('type') != 'ir.actions.report':
            return result
        result.update({"id": self.id, "printer_address": self.printer_address})
        return result

    def _get_readable_fields(self):
        return super()._get_readable_fields() | {"id", "printer_address"}

    @api.constrains("printer_address")
    def is_valid_printer_adrress(self):
        email_pattern = r"[^@]+@[^@]+\.[^@]+"
        ip_pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
        supported_ip_reports = ["product.report_productTemplatelabel_epson"]
        for record in self:
            if record.printer_address and not (re.match(email_pattern, record.printer_address) or re.match(ip_pattern, record.printer_address)):
                raise ValidationError(_(
                    "Printer address must be a valid email or IP address.\n"
                    "Example: printer@example.com or 192.168.1.10"
                ))
            if record.printer_address and re.match(ip_pattern, record.printer_address) and record.report_name not in supported_ip_reports:
                raise ValidationError(
                    _("You cannot link an IP-mode printer to a report that is not a supported label print.")
                )
