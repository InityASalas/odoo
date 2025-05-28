from odoo import models, fields, api, _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    l10n_ar_document_type_id = fields.Many2one(
        comodel_name='l10n_latam.document.type',
        string="Document Type",
        domain=lambda self: [('id', 'in', self._get_allowed_document_type_ids())],
        help="Argentina: Select the document type to be assigned on the Remito"
    )
    l10n_ar_cai_authorization_code = fields.Char(
        string="CAI",
        help="Argentina: Add the CAI number for Remitos given by ARCA",
    )
    l10n_ar_cai_expiration_date = fields.Date(
        string="CAI Expiration Date",
        help="Argentina: Add the CAI expiration date given by ARCA for the sequence configured here",
    )
    l10n_ar_sequence_number_start = fields.Char(
        string="Sequence From",
        help="Argentina: Add the first sequence number given by ARCA for this CAI",
    )
    l10n_ar_sequence_number_end = fields.Char(
        string="Sequence To",
        help="Argentina: Add the last sequence number given by ARCA for this CAI",
    )
    l10n_ar_delivery_sequence_prefix = fields.Char(
        string="Delivery Guide Prefix",
        copy=False,
        default='00001',
        help="Argentina: Prefix for the delivery guide sequence number. It is used to generate the delivery guide number.",
    )
    l10n_ar_next_delivery_number = fields.Integer(
        string="Next Delivery Guide Number",
        copy=False,
        readonly=False,
        default=1,
        related='l10n_ar_sequence_id.number_next',
        help="Argentina: Hold the next sequence to use as delivery guide number.",
    )
    l10n_ar_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string="Delivery Guide Number Sequence",
        help="Argentina: Hold the sequence to generate a delivery guide number.",
    )
    country_code = fields.Char(related='company_id.account_fiscal_country_id.code')

    # -------------------------------------------------------------------------
    # Business Logic
    # -------------------------------------------------------------------------

    def _get_allowed_document_type_ids(self):
        """Limit document types to only those used for Remitos in Argentina"""
        return [
            self.env.ref('l10n_ar.dc_r_r').id,
            self.env.ref('l10n_ar.dc_remito_x').id
        ]

    def _l10n_ar_create_delivery_guide_sequence(self):
        """
        Generate the delivery guide sequence for the picking type.
        """
        for picking_type in self.filtered(
            lambda pt: pt.company_id.country_id.code == 'AR'
            and pt.code == 'outgoing'
            and pt.l10n_ar_document_type_id
            and not pt.l10n_ar_sequence_id
        ):
            picking_type.l10n_ar_sequence_id = self.env['ir.sequence'].sudo().create({
                'name': _('%(company)s Sequence %(code)s',
                          company=picking_type.company_id.name,
                          code=picking_type.l10n_ar_delivery_sequence_prefix),
                'company_id': picking_type.company_id.id,
                'padding': 8,
                'implementation': 'no_gap',
            })
        return self

    @api.model_create_multi
    def create(self, vals_list):
        """
        Extends for creating or updating the sequence for the delivery guide number.
        """
        picking_types = super().create(vals_list)
        picking_types._l10n_ar_create_delivery_guide_sequence()
        return picking_types

    def write(self, vals):
        """
        Extends for updating the sequence for the delivery guide number when the delivery sequence prefix changes.
        """
        res = super().write(vals)
        picking_types = self - self._l10n_ar_create_delivery_guide_sequence()
        for picking_type in picking_types:
            if 'l10n_ar_delivery_sequence_prefix' in vals and picking_type.l10n_ar_sequence_id:
                picking_type.sudo().l10n_ar_sequence_id.write({
                    'name': _('%(company)s Sequence %(code)s',
                              company=picking_type.company_id.name,
                              code=picking_type.l10n_ar_delivery_sequence_prefix,
                              ),
                })
        return res
