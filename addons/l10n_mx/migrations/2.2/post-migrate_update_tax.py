# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, SUPERUSER_ID
from odoo.addons.account.models.chart_template import update_taxes_from_templates


def migrate(cr, version):
    # Create new accounts for each MX company if accounts with relevant codes aren't already present
    # Create DIOT 2025 taxes dependent on these accounts
    env = api.Environment(cr, SUPERUSER_ID, {})
    new_account_list = [
        {
            'name': "IVA acreditable pagado al 8%",
            'code': '118.01.02',
            'account_type': 'asset_current',
            'reconcile': False,
            'tag_ids': [env.ref('l10n_mx.tag_debit_balance_account').id],
        },
        {
            'name': "IVA acreditable de importación pagado",
            'code': '118.02.01',
            'account_type': 'asset_current',
            'reconcile': False,
            'tag_ids': [env.ref('l10n_mx.tag_debit_balance_account').id],
        },
        {
            'name': "IVA de importación pendiente de pago",
            'code': '119.02.01',
            'account_type': 'asset_current',
            'reconcile': True,
            'tag_ids': [env.ref('l10n_mx.tag_debit_balance_account').id],
        },
        {
            'name': "Otros impuestos y derechos",
            'code': '601.58.01',
            'account_type': 'expense',
            'reconcile': False,
            'tag_ids': [env.ref('l10n_mx.tag_debit_balance_account').id],
        }
    ]
    for company in env['res.company'].search([('chart_template_id', '=', env.ref('l10n_mx.mx_coa').id)]):
        env['account.chart.template'].try_loading(company)
        for account in new_account_list:
            new_account = {'values': account.copy()}
            new_account['values']['company_id'] = company.id
            existing_account = env['account.account'].search([('code', '=', new_account['values']['code']), ('company_id', '=', company.id)])
            if not existing_account:
                env['account.account']._load_records([new_account])
    update_taxes_from_templates(cr, 'l10n_mx.mx_coa')
