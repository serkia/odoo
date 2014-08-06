from openerp.osv import osv, fields


class Lead(osv.Model):

	_name = "website.crm.score"

	_columns = {
		'name' : fields.char("Name"),
		'score' : fields.float("Score"),
	}