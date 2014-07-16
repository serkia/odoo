# -*- coding: utf-8 -*-
{
    'name': 'Project Rating',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
This module Allows a customer to give rating on Project.
""",
    'author': 'OpenERP SA',
    'website': 'http://openerp.com',
    'depends': [
        'rating',
        'project'
    ],
    'data': [
        'project_data.xml',
        'project_view.xml',
    ],
    'demo': ['project_demo.xml'],
    'installable': True,
    'auto_install': True,
    'bootstrap': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
