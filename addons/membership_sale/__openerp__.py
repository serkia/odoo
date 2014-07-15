{
    'name': 'Membership Sale',
    'version': '0.1',
    'category': 'Tools',
    'description': """
On CONFIRM sale order create membership line.

""",
    'author': 'OpenERP SA',
    'depends': ['membership', 'sale'],
    'data': [
        'membership_sale_view.xml',
    ],
    'test': ['test/test_membership_sale.yml'],
    'installable': True,
    'auto_install': True
}

