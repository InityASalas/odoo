# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('-at_install', 'post_install')
class TestSaleOrderPaymentLink(SaleCommon):

    def test_dupa(self):
        x = 1

    def test_redirect_if_amount_lower_than_preopayment(self):


        x = 1
    def test_no_button_if_canceled(self):

        x = 1
    def test_full_link_amount(self):
        # installment/downpayment = false
        x = 1
    def test_prepayment_amount(self):
        # installment/downpayment = true
        x = 1
    def test_higher_than_prepayment_amount(self):
        # installment/downpayment = true
        # payment_amount > prepayment_amount
        x = 1

    def test_try_generate_below_prepayment_amount(self):
        x=1
