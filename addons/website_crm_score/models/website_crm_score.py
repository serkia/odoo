# REM : WHY NOT WITH NEW API ?


from openerp.osv import osv
from openerp import api, fields, models, _


class website_crm_score(osv.Model):
    _name = "website.crm.score"

    # Old API
    # _columns = {
    #     'name': fields.char("Name"),
    #     'score': fields.float("Score"),
    #     'view_ids': fields.one2many('ir.ui.view', 'score_id', string='Viewsss')
    # }

    # New API
    name = fields.Char("Name")
    score  = fields.Float("Score")
    view_ids = fields.One2many('ir.ui.view', 'score_id', string='Viewsss')