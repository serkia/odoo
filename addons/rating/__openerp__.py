# -*- coding: utf-8 -*-

{
    'name': 'Customer Rating',
    'version': '1.0',
    'category': 'Tools',
    'description': """
This module Allows a customer to give rating.
""",
    'author': 'OpenERP SA',
    'website': 'http://openerp.com',
    'depends': [
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'rating_view.xml',
        'views/rating_template.xml',
     ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'bootstrap': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
