# -*- coding: utf-8 -*-

{
    'name': 'Print Sale',
    'summary': 'Print and Send Sale Orders',
    'category': 'Tools',
    'version': '1.0',
    'description': """Print and Send your Sale Order by Post""",
    'author': 'OpenERP SA',
    'depends': ['print', 'sale'],
    'data': [
        'views/print_sale.xml'
    ],
    'installable': True,
    'auto_install': True,
}
