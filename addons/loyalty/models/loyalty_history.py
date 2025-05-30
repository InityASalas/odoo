# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools import float_round


class LoyaltyHistory(models.Model):
    _name = 'loyalty.history'
    _description = "History for Loyalty cards and Ewallets"
    _order = 'id desc'

    card_id = fields.Many2one(
        comodel_name='loyalty.card',
        required=True,
        index=True,
        ondelete='cascade',
        readonly=True,
    )
    company_id = fields.Many2one(related='card_id.company_id')

    description = fields.Text(required=True, readonly=True)

    available_issued_points = fields.Float()
    issued = fields.Float(readonly=True)
    used = fields.Float(readonly=True)

    order_model = fields.Char(readonly=True)
    order_id = fields.Many2oneReference(model_field='order_model', readonly=True)
    is_line_expired = fields.Selection(
        selection=[
            ('expired', "Expired"),
            ('valid', "Valid"),
        ],
        default='valid',
    )
    expiry_date = fields.Datetime()

    def _get_order_portal_url(self):
        self.ensure_one()
        return False

    def _get_order_description(self):
        self.ensure_one()
        return self.env[self.order_model].browse(self.order_id).display_name

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()

        for vals in vals_list:
            if 'expiry_date' not in vals:
                card_id = vals.get('card_id')
                card = self.env['loyalty.card'].browse(card_id)
                expire_after = card.program_id.expire_after
                if expire_after:
                    vals['expiry_date'] = now + timedelta(days=expire_after)

        return super().create(vals_list)

    @api.model
    def _cron_expire_loyalty_points(self):
        """
        Expire loyalty points, history lines and recompute total balance.
        """
        now = datetime.now()
        expired_history_lines = self.search([
            ('expiry_date', '<=', now),
            ('is_line_expired', '=', 'valid'),
        ])
        for line in expired_history_lines:
            if line.available_issued_points:
                points_left = float_round(line.available_issued_points, precision_digits=2)
                line.card_id.points = (
                    float_round(line.card_id.points, precision_digits=2) - points_left
                )
                line.available_issued_points = 0
            line.is_line_expired = 'expired'

    def redeem_loyalty_points(self, used_points):
        """
        Redeems loyalty points by utilizing the oldest earned points first.

        This ensures that points are consumed in the order they were earned.
        """
        def _redeem_from_history_lines(history_lines, points_to_redeem):
            redeemable_history_lines = history_lines.filtered(
                lambda history_line: history_line.is_line_expired == 'valid'
                and history_line.available_issued_points > 0,
            )
            sorted_history_lines = redeemable_history_lines.sorted(
                key=lambda history_line: (
                    history_line.expiry_date is False,
                    history_line.expiry_date,
                    history_line.id,
                ),
            )

            for history_line in sorted_history_lines:
                redeemable_points = min(history_line.available_issued_points, points_to_redeem)
                history_line.available_issued_points -= redeemable_points
                points_to_redeem -= redeemable_points

        def _redeem_points_by_card_id(self, card_id, points):
            if not card_id or points <= 0:
                return

            history_lines = self.search([('card_id', '=', card_id)])
            if history_lines:
                _redeem_from_history_lines(history_lines, points)

        if isinstance(used_points, list):
            for coupon in used_points:
                card_id = coupon.get('card_id')
                points_to_redeem = coupon.get('points_to_redeem', 0.0)

                _redeem_points_by_card_id(self, card_id, points_to_redeem)

        elif isinstance(used_points, (float, int)):
            _redeem_points_by_card_id(self, self.card_id.id, used_points)
