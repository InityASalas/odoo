from odoo import fields, models


class StockReference(models.Model):
    _name = 'stock.reference'
    _description = 'Reference between documents'

    name = fields.Char('Reference', required=True)
    move_ids = fields.Many2many(
        'stock.move', 'stock_reference_move_rel', 'reference_id', 'move_id', string="Stock Moves")
