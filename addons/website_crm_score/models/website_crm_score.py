from openerp.osv import osv
from openerp import fields


class website_crm_score(osv.Model):
    _name = "website.crm.score"

    # Old API
    # _columns = {
    #     'name': fields.char("Name")
    #     'score': fields.float("Score"),
    #     'view_ids': fields.one2many('ir.ui.view', 'score_id', string='Viewsss')
    # }

    # New API
    name = fields.Char("Name")
    score = fields.Float("Score")
    view_ids = fields.One2many('ir.ui.view', 'score_id', string='Viewsss')

    def score_exists(self, cr, uid, ids, name, context=None):  # page_exists(self, cr, uid, ids, name, module='website', context=None):
        scores = self.pool['website.crm.score'].search_read(cr, uid, domain=[], fields=['name'], context=context)
        exists = False
        name = name.lower()
        for score in scores:
            if name == score['name'].lower():
                exists = True
                break
        return exists

    def search_scores(self, cr, uid, ids, needle=None, limit=None, context=None):
        scores = self.pool['website.crm.score'].search_read(cr, uid, domain=[], fields=['name'], limit=limit, context=context)
        needle = needle.lower()
        matching_scores = [score for score in scores if needle in score['name'].lower()]
        return matching_scores

    def create_score(self, cr, uid, vals, context=None):
        print "score creation"
        print vals
        values = {
            'name': vals.get('name'),
            'score': vals.get('value'),
        }
        return self.create(cr, uid, values, context=context)
