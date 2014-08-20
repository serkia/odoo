from openerp import fields, api, models  # api


class website_crm_score(models.Model):
    _name = "website.crm.score"

    # New API
    name = fields.Char("Name")
    score = fields.Float("Score")
    view_ids = fields.One2many('ir.ui.view', 'score_id', string='Views')

    _sql_constraints = [
        ('name_unique', 'unique (name)', "The name must be unique"),
    ]

    def copy(self, cr, uid, id, default, context=None):
        score = self.browse(cr, uid, id, context=context)
        new_name = "Copy of %s" % score.name
        # =like is the original LIKE operator from SQL
        others_count = self.search(cr, uid, [('name', '=like', new_name + '%')], count=True, context=context)
        if others_count > 0:
            new_name = "%s (%s)" % (new_name, others_count + 1)
        default['name'] = new_name
        return super(website_crm_score, self).copy(cr, uid, id, default, context=context)

    @api.model
    def score_exists(self, ids, name):  # page_exists(self, cr, uid, ids, name, module='website', context=None):
        scores = self.search_read(domain=[], fields=['name'])
        exists = False
        name = name.lower()
        for score in scores:
            if name == score['name'].lower():
                exists = True
                break
        return exists

    @api.model
    def search_scores(self, ids, needle=None, limit=None):
        scores = self.search_read(domain=[], fields=['name'], limit=limit)
        needle = needle.lower()
        matching_scores = [score for score in scores if needle in score['name'].lower()]
        return matching_scores

    # todo: change to new api
    def create_score(self, cr, uid, vals, context=None):
        values = {
            'name': vals.get('name'),
            'score': vals.get('value'),
        }
        return self.create(cr, uid, values, context=context)

    # todo: change to new api
    def name_get(self, cr, uid, ids, context=None):
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            name = name + (' (%g)' % (record.score))
            res.append((record.id, name))
        return res
