# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _compute_authorship(self):
        super()._compute_authorship()
        # mail's author lookup can mix up partners with identical email addresses,
        # this override ensures the author is set to the partner responsible for the sale order
        for composer in self.filtered(lambda c: c.model == 'sale.order'):
            res_ids = composer._evaluate_res_ids()
            order_sudo = self.env['sale.order'].sudo().browse(res_ids[:1])
            author_sudo = (order_sudo.user_id or order_sudo.company_id).partner_id
            if author_sudo and author_sudo != composer.author_id:
                composer.write({
                    'author_id': author_sudo.id,
                    'email_from': author_sudo.email_formatted,
                })

    def _prepare_mail_values_static(self):
        values = super()._prepare_mail_values_static()
        if self.model == 'sale.order' and self.env.context.get('mark_so_as_sent'):
            values['mark_so_as_sent'] = True
        return values
