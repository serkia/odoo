from openerp.osv import osv
from openerp import api, models, fields


class Lead(osv.Model):

	_inherit = 'crm.lead'
	
	# Old API
	# def _compute_score(self, cr, uid, ids, field, arg, context=None):
	# 	r = {}
	# 	for lead in  self.browse(cr, uid, ids, context=context):
	# 		s=0
	# 		print lead
	# 		for score in lead.score_ids:
	# 			s += score.value
	# 		print s
	# 		r[lead.id] = s
	# 	print r
	# 	return r

	# _columns = {
	# 	'score' : fields.function(_compute_score, type='float', string='Score', store=True),
	# 	'score_ids' : fields.many2many('crm.score', 'crm_score_rel', 'lead_id', 'score_id', 'Scores'),
	# }

	# New API
	@api.one
	def _compute_score(self):
		s=0
		for score in self.score_ids:
			s += score.value
		self.score = s

	score = fields.Float(compute='_compute_score')
	score_ids = fields.Many2many('website.crm.score', 'crm_score_rel', 'lead_id', 'score_id', 'Scores')

	