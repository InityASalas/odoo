# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPutInPack(models.TransientModel):
    _name = 'stock.put.in.pack'
    _description = 'Put In Pack Wizard'

    location_dest_id = fields.Many2one('stock.location', 'Destination')
    move_line_ids = fields.Many2many('stock.move.line', string='Move lines')
    package_ids = fields.Many2many('stock.package', string='Packages')
    package_name = fields.Char('Pre-Printed Label')
    package_type_id = fields.Many2one('stock.package.type', 'Package Type')
    identification_method = fields.Selection(related="package_type_id.identification_method")
    result_package_id = fields.Many2one('stock.package', 'Package')
    origin_package_ids = fields.Many2many('stock.package', compute='_compute_origin_package_ids')
    sequence_msg = fields.Text('Sequence Description', compute='_compute_sequence_msg')

    def _compute_origin_package_ids(self):
        for wizard in self:
            packages = wizard.package_ids
            if wizard.move_line_ids:
                packages |= wizard.move_line_ids.result_package_id
            wizard.origin_package_ids = packages.parent_package_id

    @api.depends('package_type_id')
    def _compute_sequence_msg(self):
        for wizard in self:
            if wizard.package_type_id.identification_method == 'auto' and wizard.package_type_id.sequence_id:
                seq = wizard.package_type_id.sequence_id
                wizard.sequence_msg = self.env._("New package will follow a specific sequence for its number defined on the %(package_type)s type (e.g. %(sequence_value)s).",
                                                 package_type=wizard.package_type_id.name, sequence_value=seq.get_next_char(seq.number_next_actual))
            else:
                wizard.sequence_msg = ''

    @api.onchange('package_type_id')
    def _onchange_package_type_id(self):
        if self.package_type_id and self.result_package_id and self.result_package_id.package_type_id != self.package_type_id:
            self.result_package_id = False
        if self.package_type_id and self.package_type_id.identification_method != 'manual':
            self.package_name = False

    def action_put_in_pack(self):
        kwargs = self._get_put_in_pack_kwargs()
        if self.package_ids:
            return self.package_ids.action_put_in_pack(**kwargs)
        return self.move_line_ids.action_put_in_pack(from_package_wizard=True, **kwargs)

    def _get_put_in_pack_kwargs(self):
        kwargs = {
            'package_type_id': self.package_type_id.id,
            'package_id': self.result_package_id.id,
        }
        if self.package_type_id.identification_method == 'manual' and self.package_name:
            kwargs['package_name'] = self.package_name
        return kwargs
