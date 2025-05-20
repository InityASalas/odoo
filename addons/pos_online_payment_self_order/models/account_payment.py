from odoo import models, api, SUPERUSER_ID


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'pos.load.mixin']

    def send_refund_request(self, amount):
        self.ensure_one()
        refund_tx = self.payment_transaction_id.with_user(SUPERUSER_ID)._send_refund_request(amount)
        if not refund_tx:
            return False
        return refund_tx.id

    def get_account_payment_id(self, payment_transaction_id):
        return self.search([('payment_transaction_id', '=', payment_transaction_id)], limit=1).id

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['id']
