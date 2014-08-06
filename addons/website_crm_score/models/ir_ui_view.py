from openerp.osv import osv
from openerp import api, models, fields



class view(osv.osv):
    _inherit = "ir.ui.view"
    
    # Old API
    # _columns = {
    #     'website_scores': fields.many2one("crm.score", "List of scores"),
    # }

    # New API
    score_id = fields.Many2one('website.crm.score', string="Score")