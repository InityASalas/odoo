from odoo import _, api, models
from odoo.exceptions import UserError


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_posted_pdf_invoices(self):
        '''
        Prevents unlinking of invoice pdfs linked to an invoice that is posted.
        '''
        if any(move.country_code == 'SA' and move.state == 'posted' for move in self._get_posted_pdf_restricted_moves()):
            raise UserError(_("Oops! The PDF cannot be deleted according to ZATCA rules"))

    def _get_posted_pdf_restricted_moves(self):
        '''
        Returns the moves to check whether they can be unlinked.
        '''
        return self.env['account.move'].browse(self.filtered(lambda rec: rec.res_model == 'account.move' and rec.res_field == 'invoice_pdf_report_file').mapped('res_id'))
