from openerp.osv import osv, fields


class Lead(osv.Model):

	_inherit = 'crm.lead'
	
	_columns = {
		'score' : fields.integer("Score"),
	}

	_defaults = {
		'score' : 2,
	}