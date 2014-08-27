from openerp.osv import osv
from openerp import api, fields, models
from passlib.context import CryptContext

crypt_context = CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha1', 'md5_crypt'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Debian only provides 1.5 so...
    deprecated=['md5_crypt'],
)
secret_key = '12345'


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
            self.score += score_id.value

    score = fields.Float(compute='_compute_score')
    # score_ids = fields.Many2many('website.crm.score', 'crm_lead_score_date_rel', 'lead_id', 'score_id', 'Scores')
    score_ids = fields.Many2many('website.crm.score', 'crm_lead_score_rel', 'lead_id', 'score_id', string='Score')
    pageview_ids = fields.One2many('website.crm.pageview', 'lead_id', string='Page Views')
    language = fields.Many2one('res.lang', string='Language')
    assign_date = fields.Datetime(string='Assign Date')

    def signed_lead_id(self, lead_id):
        encrypted_lead_id = crypt_context.encrypt(str(lead_id) + secret_key)
        return str(lead_id) + '#' + encrypted_lead_id

    def verify_lead_id(self, cookie_content):
        if cookie_content:
            lead_id, encrypted_lead_id = cookie_content.split('#', 1)
            if crypt_context.verify(lead_id+secret_key, encrypted_lead_id):
                return lead_id
            else:
                return None
