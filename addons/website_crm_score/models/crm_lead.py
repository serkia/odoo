from openerp.osv import osv
from openerp import api, fields, models


class crm_lead_score_date(osv.Model):
    """ Adds a state on the m2m between user and session.  """
    _name = 'crm_lead_score_date'
    _table = "crm_lead_score_date_rel"

    date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', 'Lead', required=True, ondelete="cascade")
    score_id = fields.Many2one('website.crm.score', 'Score', required=True, ondelete="cascade")


class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.one
    @api.model
    def _compute_score(self):
        # self.score = self.score_ids and sum(map(lambda x: x.id, self.score_ids)) or 0 # why ?
        # print self.env['res.lang'].search([])
        self.score = 0
        for score_id in self.score_ids:
            self.score += score_id.score

    score = fields.Float(compute='_compute_score')
    score_ids = fields.Many2many('website.crm.score', 'crm_lead_score_date_rel', 'lead_id', 'score_id', 'Scores')
    language = fields.Many2one('res.lang', string='Language')
