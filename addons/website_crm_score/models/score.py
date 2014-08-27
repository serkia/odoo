from openerp import fields, models, SUPERUSER_ID
from openerp.tools.safe_eval import safe_eval


class score(models.Model):
    _name = 'website.crm.score'

    # New API
    name = fields.Char('Name', required=True)
    value = fields.Float('Value', required=True)
    domain = fields.Char('Domain', required=True)
    running = fields.Boolean('Active', default=True)

    # @api.model
    # @api.multi
    def assign_scores_to_leads(self, cr, uid, ids=[], context=None):

        def add_to_dict(d, k, v):
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]

        scores = self.search_read(cr, uid, domain=[('running', '=', True)], fields=['name', 'domain', 'value'], context=None)
        scores_to_write = {}
        for score in scores:
            domain = safe_eval(score['domain'])
            domain.extend([('user_id', '=', False)])
            leads = self.pool['crm.lead'].search_read(cr, uid, domain=domain, fields=['name', 'country_id', 'language', 'score_ids'], context=None)
            for lead in leads:
                if not score['id'] in lead['score_ids']:
                    # todo: isn't there a nice way to do so ?
                    add_to_dict(scores_to_write, lead['id'], (4, score['id']))

        # print scores_to_write

        for lead_id, data in scores_to_write.iteritems():
            lead_record = self.pool['crm.lead'].browse(cr, SUPERUSER_ID, lead_id, context=None)
            lead_record.write({'score_ids': data})
