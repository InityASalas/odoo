# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class PaymentLinkWizard(models.TransientModel):
    _inherit = 'payment.link.wizard'
    _description = 'Generate Sales Payment Link'

    amount_paid = fields.Monetary(string="Already Paid", readonly=True)
    confirmation_message = fields.Char(compute='_compute_confirmation_message')
    prepayment_amount = fields.Monetary(currency_field='currency_id')

    @api.depends('amount')
    def _compute_confirmation_message(self):
        self.confirmation_message = False
        for wizard in self.filtered(lambda w: w.res_model == 'sale.order'):
            sale_order = wizard.env['sale.order'].sudo().browse(wizard.res_id)
            if sale_order.state in ('draft', 'sent') and sale_order.require_payment:
                wizard.confirmation_message = _("This payment will confirm the quotation.")

    @api.depends('res_model', 'res_id')
    def _compute_warning_message(self):
        sale_wizard = self.env['payment.link.wizard']
        for wizard in self:
            if wizard.res_model != 'sale.order':
                continue
            if wizard.amount < wizard.prepayment_amount:
                wizard.warning_message = _(
                    "You cannot generate a link for payment lower than prepayment amount."
                )
                sale_wizard |= wizard
        super(PaymentLinkWizard, self - sale_wizard)._compute_warning_message()

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

        return {
            'payment_amount': self.amount,
        }
