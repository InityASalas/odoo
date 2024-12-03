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

    def _decode_attachment(self, file_data, new=False):
        if file_data['import_file_type'] == 'account.edi.xml.oioubl_201':
            return self.env['account.edi.xml.oioubl_201']._import_invoice_ubl_cii(self, file_data, new)
        return super()._decode_attachment(file_data, new)

    def _get_import_priority(self, file_data):
        if file_data['import_file_type'] == 'account.edi.xml.oioubl_201':
            return 20
        return super()._get_import_priority(file_data)
