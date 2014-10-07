# -*- coding: utf-8 -*-

{
    'name': 'Print Provider',
    'summary': 'Print and Send Provider Base Module',
    'category': 'Hidden',
    'version': '1.0',
    'description': """Print and Send Provider Base Module""",
    'author': 'OpenERP SA',
    'depends': ['base_setup', 'account'],
    'data': [
        'wizard/print_order_wizard.xml',
        'wizard/print_order_sendnow_wizard.xml',
        'views/print_view.xml',
        'views/res_config_view.xml',
        'views/account_invoice_view.xml',
        'data/print_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
}
