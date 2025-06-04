# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.mail.controllers import attachment
from .thread import ThreadController


class AttachmentController(attachment.AttachmentController):
    def _can_delete_attachment(self, message, **kwargs):
        return ThreadController._can_delete_attachment(
            message, **kwargs
        ) or super._can_delete_attachment(message, **kwargs)

