# Part of Odoo. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch


from odoo.exceptions import AccessError
from odoo.tests import JsonRpcException, tagged
from odoo.tools import mute_logger

from odoo.addons.account_payment.tests.common import AccountPaymentCommon
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.sale.controllers.portal import PaymentPortal
from odoo.addons.sale.tests.common import SaleCommon, SaleHttpCommon
from odoo.addons.website.tools import MockRequest


@tagged('-at_install', 'post_install')
class TestSalePayment(AccountPaymentCommon, SaleCommon, SaleHttpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Replace PaymentCommon defaults by SaleCommon ones
        cls.currency = cls.sale_order.currency_id
        cls.partner = cls.sale_order.partner_invoice_id

        cls.provider.journal_id.inbound_payment_method_line_ids.filtered(lambda l:
            l.payment_provider_id == cls.provider
        ).payment_account_id = cls.inbound_payment_method_line.payment_account_id

    def test_confirmed_transactions_comfirms_so_with_multiple_transaction(self):
        """ Test that a confirmed transaction confirms a SO even if one or more non-confirmed
        transactions are linked. """
        # Create the payment
        self.amount = self.sale_order.amount_total
        self._create_transaction(
            flow='redirect',
            sale_order_ids=[self.sale_order.id],
            state='draft',
            reference='Test Transaction Draft 1',
        )
        self._create_transaction(
            flow='redirect',
            sale_order_ids=[self.sale_order.id],
            state='draft',
            reference='Test Transaction Draft 2',
        )
        tx = self._create_transaction(flow='redirect', sale_order_ids=[self.sale_order.id], state='done')
        tx._post_process()

        self.assertEqual(self.sale_order.state, 'sale')

    def test_auto_confirm_and_auto_invoice(self):
        # Set automatic invoice
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')

        # Create the payment
        self.amount = self.sale_order.amount_total
        tx = self._create_transaction(flow='redirect', sale_order_ids=[self.sale_order.id], state='done')
        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            tx._post_process()

        self.assertEqual(self.sale_order.state, 'sale')
        self.assertTrue(tx.invoice_ids)
        self.assertTrue(self.sale_order.invoice_ids)

    def test_auto_done_and_auto_invoice(self):
        # Set automatic invoice
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')
        # Lock the sale orders when confirmed
        self.group_user.implied_ids += self.env.ref('sale.group_auto_done_setting')

        # Create the payment
        self.amount = self.sale_order.amount_total
        tx = self._create_transaction(flow='redirect', sale_order_ids=[self.sale_order.id], state='done')
        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            tx._post_process()

        self.assertEqual(self.sale_order.state, 'sale')
        self.assertTrue(self.sale_order.locked)
        self.assertTrue(tx.invoice_ids)
        self.assertTrue(self.sale_order.invoice_ids)
        self.assertTrue(tx.invoice_ids.is_move_sent)

    def test_so_partial_payment_no_invoice(self):
        # Set automatic invoice
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')

        # Create the payment
        self.amount = self.sale_order.amount_total / 10.
        tx = self._create_transaction(flow='redirect', sale_order_ids=[self.sale_order.id], state='done')
        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            tx._post_process()

        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(tx.invoice_ids)
        self.assertFalse(self.sale_order.invoice_ids)

    def test_already_confirmed_so_payment(self):
        # Set automatic invoice
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')

        # Confirm order before payment
        self.sale_order.action_confirm()

        # Create the payment
        self.amount = self.sale_order.amount_total
        tx = self._create_transaction(flow='redirect', sale_order_ids=[self.sale_order.id], state='done')
        tx._post_process()

        self.assertTrue(tx.invoice_ids)
        self.assertTrue(self.sale_order.invoice_ids)

    def test_invoice_is_final(self):
        """Test that invoice generated from a payment are always final"""
        # Set automatic invoice
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')

        # Create the payment
        self.amount = self.sale_order.amount_total
        tx = self._create_transaction(
            flow='redirect',
            sale_order_ids=[self.sale_order.id],
            state='done',
        )
        with mute_logger('odoo.addons.sale.models.payment_transaction'), patch(
            'odoo.addons.sale.models.sale_order.SaleOrder._create_invoices',
            return_value=self.env['account.move']
        ) as _create_invoices_mock:
            tx._post_process()

        self.assertTrue(_create_invoices_mock.call_args.kwargs['final'])

    def test_linked_transactions_when_invoicing(self):
        self.provider.support_manual_capture = 'partial'
        partial_amount = self.sale_order.amount_total - 2

        partial_tx_done = self._create_transaction(
            flow='direct',
            amount=partial_amount,
            sale_order_ids=[self.sale_order.id],
            state='done',
            reference='partial_tx_done',
        )
        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            partial_tx_done._post_process()
        partial_tx_pending = self._create_transaction(
            flow='direct',
            amount=2,
            sale_order_ids=[self.sale_order.id],
            state='pending',
            reference='partial_tx_pending',
        )
        self.assertTrue(partial_tx_done.payment_id, msg="Account payment should have been created.")
        msg = "The created account payment shouldn't be reconciled as there are no invoice yet."
        self.assertFalse(partial_tx_pending.payment_id.is_reconciled, msg=msg)

        # Add some noisy transactions
        self._create_transaction(
            flow='direct', sale_order_ids=[self.sale_order.id], state='draft', reference='draft_tx'
        )
        self._create_transaction(
            flow='direct', sale_order_ids=[self.sale_order.id], state='error', reference='error_tx'
        )
        self._create_transaction(
            flow='direct', sale_order_ids=[self.sale_order.id], state='cancel', reference='cncl_tx'
        )

        msg = "The sale order should be linked to 5 transactions."
        self.assertEqual(len(self.sale_order.transaction_ids), 5, msg=msg)

        self.sale_order.action_confirm()
        self.sale_order._create_invoices()

        self.assertEqual(len(self.sale_order.invoice_ids), 1, msg="1 invoice should be created.")

        first_invoice = self.sale_order.invoice_ids
        linked_txs = first_invoice.transaction_ids
        msg = "The newly created invoice should be linked to the done and pending transactions."
        self.assertEqual(len(linked_txs), 2, msg=msg)
        expected_linked_tx = (partial_tx_done, partial_tx_pending)
        self.assertTrue(all(tx in expected_linked_tx for tx in linked_txs), msg=msg)
        msg = "The payment shouldn't be reconciled yet."
        self.assertFalse(partial_tx_done.payment_id.is_reconciled, msg=msg)

        partial_tx_done._post_process()

        msg = "The payment should now be reconciled."
        self.assertTrue(partial_tx_done.payment_id.is_reconciled, msg=msg)

        self.sale_order.order_line[0].product_uom_qty += 2
        self.sale_order._create_invoices()

        second_invoice = self.sale_order.invoice_ids - first_invoice
        msg = "The newly created invoice should only be linked to the pending transaction."
        self.assertEqual(len(second_invoice.transaction_ids), 1, msg=msg)
        self.assertEqual(second_invoice.transaction_ids.state, 'pending', msg=msg)

    def test_downpayment_confirm_sale_order_sufficient_amount(self):
        """Paying down payments can confirm an order if amount is enough."""
        self.sale_order.require_payment = True
        self.sale_order.prepayment_percent = 0.1
        order_amount = self.sale_order.amount_total

        tx = self._create_transaction(
            flow='direct',
            amount=order_amount * self.sale_order.prepayment_percent,
            sale_order_ids=[self.sale_order.id],
            state='done',
        )
        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            tx._post_process()

        self.assertTrue(self.sale_order.state == 'sale')

    def test_downpayment_automatic_invoice(self):
        """
        Down payment invoices should be created when a down payment confirms
        the order and automatic invoice is checked.
        """
        self.sale_order.require_payment = True
        self.sale_order.prepayment_percent = 0.2
        self.env['ir.config_parameter'].sudo().set_param('sale.automatic_invoice', 'True')

        tx = self._create_transaction(
            flow='direct',
            amount=self.sale_order.amount_total * self.sale_order.prepayment_percent,
            sale_order_ids=[self.sale_order.id],
            state='done')

        with mute_logger('odoo.addons.sale.models.payment_transaction'):
            tx._post_process()

        invoice = self.sale_order.invoice_ids
        self.assertTrue(len(invoice) == 1)
        self.assertTrue(invoice.line_ids[0].is_downpayment)

    def test_check_portal_access_token_before_rerouting_flow(self):
        """ Test that access to the provided sales order is checked against the portal access token
        before rerouting the payment flow. """
        payment_portal_controller = PaymentPortal()

        with patch.object(CustomerPortal, '_document_check_access') as mock:
            payment_portal_controller._get_extra_payment_form_values()
            self.assertEqual(
                mock.call_count, 0, msg="No check should be made when sale_order_id is not provided."
            )

            mock.reset_mock()

            payment_portal_controller._get_extra_payment_form_values(
                sale_order_id=self.sale_order.id, access_token='whatever'
            )
            self.assertEqual(
                mock.call_count, 1, msg="The check should be made as sale_order_id is provided."
            )

    def test_check_payment_access_token_before_rerouting_flow(self):
        """ Test that access to the provided sales order is checked against the payment access token
        before rerouting the payment flow. """
        payment_portal_controller = PaymentPortal()

        def _document_check_access_mock(*_args, **_kwargs):
            raise AccessError('')

        with patch.object(
            CustomerPortal, '_document_check_access', _document_check_access_mock
        ), patch('odoo.addons.payment.utils.check_access_token') as check_payment_access_token_mock:
            try:
                payment_portal_controller._get_extra_payment_form_values(
                    sale_order_id=self.sale_order.id, access_token='whatever'
                )
            except Exception:
                pass  # We don't care if it runs or not; we only count the calls.
            self.assertEqual(
                check_payment_access_token_mock.call_count,
                1,
                msg="The access token should be checked again as a payment access token if the"
                    " check as a portal access token failed.",
            )

    @mute_logger('odoo.http')
    def test_transaction_route_rejects_unexpected_kwarg(self):
        url = self._build_url(f'/my/orders/{self.sale_order.id}/transaction')
        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'partner_id': self.partner.id,  # This should be rejected.
        }
        with self.assertRaises(JsonRpcException, msg='odoo.exceptions.ValidationError'):
            self.make_jsonrpc_request(url, route_kwargs)

    def test_partial_payment_confirm_order(self):
        """
        Test that a sale order can be confirmed through partial payments and that
        correct mails are sent each time.
        """

        self.amount = self.sale_order.amount_total / 2

        with patch(
            'odoo.addons.sale.models.sale_order.SaleOrder._send_order_notification_mail',
        ) as notification_mail_mock:
            tx_pending = self._create_transaction(
                flow='direct',
                sale_order_ids=[self.sale_order.id],
                state='pending',
                reference='Test Transaction Draft 1',
            )

            self.assertEqual(self.sale_order.state, 'draft')

            tx_pending._set_done()
            tx_pending._post_process()

            self.assertEqual(notification_mail_mock.call_count, 1)
            notification_mail_mock.assert_called_once_with(
                self.env.ref('sale.mail_template_sale_payment_executed'))
            self.assertEqual(self.sale_order.state, 'draft')
            self.assertEqual(self.sale_order.amount_paid, self.amount)

            tx_done = self._create_transaction(
                flow='direct',
                sale_order_ids=[self.sale_order.id],
                state='done',
                reference='Test Transaction Draft 2',
            )
            tx_done._post_process()

            self.assertEqual(notification_mail_mock.call_count, 2)
            notification_mail_mock.assert_called_with(
                self.env.ref('sale.mail_template_sale_confirmation'))
            self.assertEqual(self.sale_order.state, 'sale')

    def test_link_payment(self):
        """ Payment link should allow payment for quotation."""

        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'payment_amount': self.sale_order.amount_total
        }

        res = self._link_payment(self.sale_order, route_kwargs)

        self.assertEqual(res.status_code, 200, "Response should = OK")
        content = res.content.decode('utf-8')

        self.assertTrue('o_sale_portal_paynow' in content,
                         "Payment should be possible")

        tx_context = self._get_payment_context(res)
        self.assertEqual(tx_context['amount'], self.sale_order.amount_total)

    @mute_logger('odoo.http')
    def test_payment_amount_below_prepayment_amount(self):
        """
        Link with payment amount below prepayment amount cannot be accepted.
        """
        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'payment_amount': 1
        }
        res = self._link_payment(self.sale_order, route_kwargs)

        self.assertEqual(res.status_code, 404, "It should refuse to render the page and redirect")

    def test_link_payment_cancelled_sale_order(self):
        """ Link with payment amount should prevent paying if SO is canceled. """
        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'payment_amount': self.sale_order.amount_total
        }

        self.sale_order.state = 'cancel'

        res = self._link_payment(self.sale_order, route_kwargs)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        content = res.content.decode('utf-8')

        self.assertFalse('o_sale_portal_paynow' in content,
                        "Payment shouldn't be possible for canceled Sale Order")

    def test_payment_link_down_payment_amount(self):
        """Test link portal payment when quotation has prepayment set."""
        self.sale_order.require_payment = True
        self.sale_order.prepayment_percent = 0.5
        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'payment_amount': self.sale_order.amount_total * 0.5
        }
        res = self._link_payment(self.sale_order, route_kwargs)

        self.assertEqual(res.status_code, 200, "Response should = OK")
        tx_context = self._get_payment_context(res)
        self.assertEqual(tx_context['amount'], self.sale_order.amount_total * 0.5)

        # simulate choosing paying full amount
        route_kwargs['amount_selection'] = 'full_amount'
        res = self._link_payment(self.sale_order, route_kwargs)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        tx_context = self._get_payment_context(res)

        self.assertEqual(tx_context['amount'], self.sale_order.amount_total)

        # simulate creating payment link for full amount when down payment is defined
        route_kwargs['payment_amount'] = self.sale_order.amount_total
        res = self._link_payment(self.sale_order, route_kwargs)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        content = res.content.decode('utf-8')
        self.assertEqual(
            'o_sale_portal_amount_prepayment_button' in content,
            "Down payment button shouldn be available even if link was generated for full amount."
        )
        tx_context = self._get_payment_context(res)
        self.assertEqual(
            tx_context['amount'],
            self.sale_order.amount_total,
            "By default, total amount should be used."
        )


        # choose down payment when link was generated for full payment
        route_kwargs['amount_selection'] = 'down_payment'
        res = self._link_payment(self.sale_order, route_kwargs)
        self.assertEqual(res.status_code, 200, "Response should = OK")
        tx_context = self._get_payment_context(res)
        self.assertEqual(tx_context['amount'], self.sale_order.amount_total * 0.5)



    def test_payment_link_sale_order(self):
        """ Ensure that payment with link is possible for confirmed Sale Order."""

        self.sale_order.state = 'sale'

        route_kwargs = {
            'access_token': self.sale_order._portal_ensure_token(),
            'payment_amount': 1
        }
        res = self._link_payment(self.sale_order, route_kwargs)

        content = res.content.decode('utf-8')
        self.assertTrue('o_sale_portal_paynow' in content,
                        "The payment button should be available.")

    def test_payment_link_generation(self):
        """
        Check if links are created correctly and if a warning is present when trying to generate
        lower than prepayment link.
        """

        self.sale_order.require_payment = True
        self.sale_order.prepayment_percent = 0.5

        payment_context = {'active_model': 'sale.order', 'active_id': self.sale_order.id}
        # payment.link.wizard needs to access request.env when it generates the access_token.
        with MockRequest(self.sale_order.env):
            # Try to generate link for amount below prepayment amount
            wiz = self.env['payment.link.wizard'].with_context(payment_context).create({
                'amount': 3
            })

        self.assertEqual(
            wiz.warning_message,
            "You cannot generate a link for payment lower than prepayment amount."
        )

        with MockRequest(self.sale_order.env):
            wiz = self.env['payment.link.wizard'].with_context(payment_context).create({})
            pay_url = wiz.link

        res = self._make_http_get_request(pay_url)

        content = res.content.decode('utf-8')
        self.assertTrue('o_sale_portal_paynow' in content,
                        "The payment button should be available.")

        tx_context = self._get_payment_context(res)
        self.assertEqual(tx_context['amount'], 362.5)
