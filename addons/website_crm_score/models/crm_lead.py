from openerp import api, fields, models
import md5


# todo: what should the secret key be ?
secret_key = '12345'


class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.one
    def _count_pageviews(self):
        self.pageviews_count = len(self.score_pageview_ids) 

    @api.one
    def _compute_score(self):
        self.score = 0
        for score_id in self.score_ids:
            self.score += score_id.value

    score = fields.Float(compute='_compute_score')
    score_ids = fields.Many2many('website.crm.score', 'crm_lead_score_rel', 'lead_id', 'score_id', string='Score')
    score_pageview_ids = fields.One2many('website.crm.pageview', 'lead_id', string='Page Views')
    # language = fields.Many2one('res.lang', string='Language')  # todo : move to crm lead
    assign_date = fields.Datetime(string='Assign Date')
    pageviews_count = fields.Integer(compute='_count_pageviews')

    def encode(self, lead_id):
        encrypted_lead_id = md5.new(str(lead_id) + secret_key).hexdigest()
        return str(lead_id) + '-' + encrypted_lead_id

    def decode(self, request):
        # opens the cookie, verifies the signature of the lead_id
        # returns lead_id if the verification passes and None otherwise
        cookie_content = request.httprequest.cookies.get('lead_id')
        if cookie_content:
            lead_id, encrypted_lead_id = cookie_content.split('-', 1)
            expected_encryped_lead_id = md5.new(lead_id + secret_key).hexdigest()
            if encrypted_lead_id == expected_encryped_lead_id:
                return int(lead_id)
            else:
                return None
