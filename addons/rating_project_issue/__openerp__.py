# -*- coding: utf-8 -*-
{
    'name': 'Issue Rating',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
This module Allows a customer to give rating on Project Issue.
""",
    'author': 'OpenERP SA',
    'website': 'http://openerp.com',
    'depends': [
        'rating',
        'project_issue'
    ],
    'data': [
        'project_issue_view.xml',
    ],
    'demo': [
        'project_issue_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'bootstrap': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
