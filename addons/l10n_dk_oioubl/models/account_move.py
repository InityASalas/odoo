from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_import_file_type(self, file_data):
        """ Identify OIOUBL files. """
        # EXTENDS 'account'
        if (
            file_data['xml_tree'] is not None
            and (customization_id := file_data['xml_tree'].findtext('{*}CustomizationID'))
            and 'OIOUBL-2' in customization_id
        ):
            return 'account.edi.xml.oioubl_201'

        return super()._get_import_file_type(file_data)

    def _get_edi_decoder(self, file_data, new=False):
        if file_data['import_file_type'] == 'account.edi.xml.oioubl_201':
            return {
                'priority': 20,
                'decoder': self.env['account.edi.xml.oioubl_201']._import_invoice_ubl_cii,
                'reason_cannot_decode': (
                    self._reason_cannot_decode_is_not_draft()
                    or self._reason_cannot_decode_has_invoice_lines()
                ),
            }
        return super()._get_edi_decoder(file_data, new)
