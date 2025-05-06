# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.http import request
from odoo.tools import format_amount


class PaymentLinkWizard(models.TransientModel):
    _inherit = 'payment.link.wizard'
    _description = 'Generate Sales Payment Link'

    amount_paid = fields.Monetary(string="Already Paid", readonly=True)
    confirmation_message = fields.Char(compute='_compute_confirmation_message')

    @api.depends('amount')
    def _compute_confirmation_message(self):
        self.confirmation_message = False
        for wizard in self.filtered(lambda w: w.res_model == 'sale.order'):
            sale_order = wizard.env['sale.order'].sudo().browse(wizard.res_id)
            if sale_order.state in ('draft', 'sent') and sale_order.require_payment:
                wizard.confirmation_message = _("This payment will confirm the quotation.")

    def _prepare_url(self, base_url, related_document):
        """ Override of `payment` to use the portal page URL. """
        res = super()._prepare_url(base_url, related_document)
        if self.res_model != 'sale.order':
            return res

        return f'{base_url}{related_document.get_portal_url()}'

    def _prepare_query_params(self, *args):
        """ Override of `payment` to add SO related values to the query params. """
        res = super()._prepare_query_params(*args)
        if self.res_model != 'sale.order':
            return res
        #pass link amount only if its < 100%

        return {
            'link_amount': self.amount,
            'showPaymentModal': 'true',
        }
