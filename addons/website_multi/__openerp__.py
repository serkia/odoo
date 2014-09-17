{
    'name': 'Multi Website',
    'category': 'Website',
    'summary': 'Build Multiple Websites',
    'website': 'https://www.odoo.com',
    'version': '1.0',
    'description': """
OpenERP Multi Website
=====================

        """,
    'author': 'OpenERP SA',
    'depends': ['website'],
    'installable': True,
    'data': [
        'views/res_config.xml',
        'views/website_views.xml',
    ],
    'demo': [
        'data/demo.xml',
    ],
    'qweb': [],
    'application': True,
}