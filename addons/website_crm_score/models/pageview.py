from openerp import fields, api, models  # api


class pageview(models.Model):
    _name = "website.crm.pageview"

    create_date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    url = fields.Char(string='Url')


