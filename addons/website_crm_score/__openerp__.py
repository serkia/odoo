{
    'name': "Lead Scoring",
    'category': "Test",
    'version': "1.0",
    'depends': ['base', 'website_crm', 'sales_team', 'marketing'],
    'author': "Me",
    'description': """\
    Lead scoring""",
    'data': [
        'views/website_crm_score.xml',
        'views/reporting.xml',
        'views/sales.xml',
        'views/marketing.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'data/website_crm_score_demo.xml',
    ],
}
