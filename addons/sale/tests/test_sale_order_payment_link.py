# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('-at_install', 'post_install')
class TestSaleOrderPaymentLink(SaleCommon):

    def test_dupa(self):
        x = 1
