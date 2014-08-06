# REM : WHY NOT WITH NEW API ?


from openerp.osv import osv, fields


class website_crm_score(osv.Model):
    _name = "website.crm.score"

    _columns = {
        'name': fields.char("Name"),
        'score': fields.float("Score"),
        'view_ids': fields.one2many('ir.ui.view', 'score_id', string='Viewsss')
    }
