{
    'name': 'Print with DocsAway',
    'summary': 'Print and Send Invoices with DocsAway.com',
    'version': '1.0',
    'category': 'Tools',
    'description': """
This module allows you to send your documents through postal mail, thanks to Docsaway.
======================================================================================
    """,
    'author': 'OpenERP SA',
    'depends': ['print'],
    'data': [
        'views/print_docsaway_view.xml',
        'data/docsaway.xml',
    ],
    'installable': True,
    'auto_install': False,
}
