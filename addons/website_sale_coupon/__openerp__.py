{
    'name': 'Sales Coupon',
    'version': '1.0',
    'category': 'Sales Coupon',
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'description': """
OpenERP Website Sales_coupon
===============================

        """,
    'depends': ['website_sale'],
    'data': [
        'website_sale_coupon_view.xml',
        'views/report_sale_coupon.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

