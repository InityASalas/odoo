# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ScheduledMessage(models.Model):
    _inherit = 'mail.scheduled.message'

    @api.model
    def _notification_parameters_whitelist(self):
        return super()._notification_parameters_whitelist() | {'mark_so_as_sent'}
