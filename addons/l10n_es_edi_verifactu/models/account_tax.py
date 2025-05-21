from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # TODO: move to l10n_es?
    def _l10n_es_get_sujeto_tax_types(self):
        return ['sujeto', 'sujeto_isp', 'sujeto_agricultura']

    def _l10n_es_edi_verifactu_get_tax_types_map(self):
        """Return dict: l10n_es_type -> verifactu tax type
        """
        VAT = '01'
        IPSI = '02'
        IGIC = '03'
        other = '05'
        return {
            'exento': VAT,
            'sujeto': VAT,
            'sujeto_agricultura': VAT,
            'sujeto_isp': VAT,
            'no_sujeto': VAT,
            'no_sujeto_loc': VAT,
            'recargo': other,
            'igic': IGIC,
            'ipsi': IPSI,
        }

    def _l10n_es_edi_verifactu_get_tax_details_functions(self, company):
        def full_filter_invl_to_apply(line):
            return any(t != 'ignore' for t in line.tax_ids.flatten_taxes_hierarchy().mapped('l10n_es_type'))

        def grouping_key_generator(base_line, tax_values):
            tax = tax_values['tax_repartition_line'].tax_id

            l10n_es_exempt_reason = tax.l10n_es_exempt_reason if tax.l10n_es_type == 'exento' else False

            # Tax t with recargo and tax t without recargo are to be kept separate for the output
            # Note: We assume there is only a single (main tax, recargo tax) pair on a single base line
            with_recargo = False
            if tax.l10n_es_type in self.env['account.tax']._l10n_es_get_sujeto_tax_types():
                with_recargo = base_line['taxes'].filtered(lambda t: t.l10n_es_type == 'recargo')

            grouping_key = {
                'amount': tax.amount,
                'with_recargo': with_recargo,
                'l10n_es_bien_inversion': tax.l10n_es_bien_inversion,
                'l10n_es_exempt_reason': l10n_es_exempt_reason,
                'l10n_es_type': tax.l10n_es_type,
            }
            return grouping_key

        def filter_to_apply(base_line, tax_values):
            return (tax_values['tax_repartition_line'].factor_percent > 0.0
                    and tax_values['tax_repartition_line'].tax_id.amount != -100.0
                    and tax_values['tax_repartition_line'].tax_id.l10n_es_type not in ('ignore', 'retencion'))

        return {
            'full_filter_invl_to_apply': full_filter_invl_to_apply,
            'grouping_key_generator': grouping_key_generator,
            'filter_to_apply': filter_to_apply,
        }
