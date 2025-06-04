# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'United States - Accounting',
    'website': 'https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations.html',
    'icon': '/account/static/description/l10n.png',
    'countries': ['us'],
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """
    """,
    'depends': ['l10n_us', 'account'],
    'data': [
        'views/res_bank_views.xml',
        'data/uom_data.xml',
    ],
    'installable': True,
    'auto_install': ['account'],
    'license': 'LGPL-3',
<<<<<<< ebf220087d1fc615dd5edf39af0114514863cde7
||||||| ae09cdf5e70b015d479e5f87e045c046e3f506e9
    'data': [
        'data/uom_data.xml',
    ],
=======
    'data': [
        'data/uom_data.xml',
        'data/tax_report.xml',
    ],
>>>>>>> 537f1ff68d82f6cd7e14ae4a2be01883401541ab
}
