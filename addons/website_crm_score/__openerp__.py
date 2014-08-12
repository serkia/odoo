{
    'name': "Lead Scoring",
    'category': "Test",
    'version': "1.0",
    'depends': ['base', 'website_crm', 'sales_team'],
    'author': "Me",
    'description': """\
    Lead scoring""",
    'data': [
        'views/lead.xml',
        'views/website_crm_score.xml',
        'views/sales.xml',
        'security/ir.model.access.csv',
    ],
}
