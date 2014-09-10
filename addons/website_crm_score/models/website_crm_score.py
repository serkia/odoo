from openerp import fields, models, api
from openerp.tools.safe_eval import safe_eval


class website_crm_score(models.Model):
    _name = 'website.crm.score'

    @api.one
    def _count_leads(self):
        self.leads_count = len(self.lead_ids)

    # New API
    name = fields.Char('Name', required=True)
    value = fields.Float('Value', required=True)
    domain = fields.Char('Domain', required=True)
    running = fields.Boolean('Active', default=True)
    lead_ids = fields.Many2many('crm.lead', 'crm_lead_score_rel', 'score_id', 'lead_id', string='Leads')
    leads_count = fields.Integer(compute='_count_leads')

    # ids is needed when the button is used to start the function,
    # the default [] is needed for the function to be usable by the cron
    @api.model
    def assign_scores_to_leads(self, ids=[]):

        def add_to_dict(d, k, v):
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]

        scores = self.search_read(domain=[('running', '=', True)], fields=['name', 'domain', 'value'])
        scores_to_write = {}
        for score in scores:
            domain = safe_eval(score['domain'])
            # ('user_id', '=', False) could be added, but the score might still be relevant when a lead is assigned ot a salesmen
            domain.extend([('date_closed', '=', False)])
            leads = self.env['crm.lead'].search_read(domain=domain, fields=['name', 'country_id', 'lang_id', 'score_ids'])
            for lead in leads:
                if not score['id'] in lead['score_ids']:
                    add_to_dict(scores_to_write, lead['id'], (4, score['id']))

        for lead_id, data in scores_to_write.iteritems():
            lead_record = self.sudo().env['crm.lead'].browse(lead_id)
            lead_record.write({'score_ids': data})
