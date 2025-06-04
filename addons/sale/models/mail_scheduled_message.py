# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import api, models


class ScheduledMessage(models.Model):
    _inherit = 'mail.scheduled.message'

    def _post_message(self, raise_exception=True):
        mark_so_as_sent = self.with_context(mark_so_as_sent=True).browse()
        for scheduled_message in self:
            notification_parameters = json.loads(scheduled_message.notification_parameters or '{}')
            if notification_parameters.pop('mark_so_as_sent', False):
                mark_so_as_sent += scheduled_message
                scheduled_message.notification_parameters = json.dumps(notification_parameters)
        if mark_so_as_sent:
            super(ScheduledMessage, mark_so_as_sent)._post_message(raise_exception)
        if remaining := self - mark_so_as_sent:
            super(ScheduledMessage, remaining)._post_message(raise_exception)

    @api.model
    def _notification_parameters_whitelist(self):
        return super()._notification_parameters_whitelist() | {'mark_so_as_sent'}
