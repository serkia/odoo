from openerp.osv import osv
from openerp import fields


class view(osv.osv):
    _inherit = "ir.ui.view"

    # Old API
    # _columns = {
    #     'website_scores': fields.many2one("crm.score", "List of scores"),
    # }

    # New API
    score_id = fields.Many2one('website.crm.score', string="Score")
    track = fields.Boolean(string='Track', default=False)
