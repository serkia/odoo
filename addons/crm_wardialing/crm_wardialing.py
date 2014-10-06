# -*- coding: utf-8 -*-

from openerp import models, fields, api



#----------------------------------------------------------
# Models
#----------------------------------------------------------





class crm_phonecall(models.Model):
	_inherit = "crm.phonecall"

	_order = "sequence, id"

	to_call = fields.Boolean("Call Center Call", default = False)
	made_call = fields.Boolean("Made Call", default = False)
	sequence = fields.Integer('Sequence', select=True, help="Gives the sequence order when displaying a list of Phonecalls.", default = 10)
	
	

	@api.multi
	def call_partner(self):
		print("CALL FUNCTION")
		print(self)
		print(self.partner_id.phone)

	
class crm_lead(models.Model):
	_inherit = "crm.lead"

	@api.one
	def create_call_center_call(self):
		
		phonecall = self.env['crm.phonecall'].create({
				'name' : self.name
				});
		phonecall.to_call = True
		phonecall.opportunity_id = self.id
		phonecall.partner_id = self.partner_id
		phonecall.state = 'pending'

class crm_wardialing_wizard(models.TransientModel):
	_name = 'crm.wardialing.wizard';

	@api.multi
	def _default_opportunity(self):
		if(self.env['crm.lead'].browse(self._context.get('active_ids'))):
			return self.env['crm.lead'].browse(self._context.get('active_ids'))
		else:
			return self.env['crm.lead'].browse(self._context.get('opportunity_id'))
		
	
	opportunity_ids = fields.Many2many('crm.lead', string="Opportunities", 
		required=True, default=_default_opportunity)

	@api.multi
	def save(self):
		for opportunity in self.opportunity_ids:
			phonecall = self.env['crm.phonecall'].create({
				'name' : opportunity.name
				});
			phonecall.to_call = True
			phonecall.opportunity_id = opportunity.id
			phonecall.partner_id = opportunity.partner_id
			phonecall.state = 'pending'
		return {}

class crm_phonecall_log_wizard(models.TransientModel):
	_name = 'crm.phonecall.log.wizard';

	@api.multi
	def _default_description(self):
		if(self._context.get('phonecall').get('description') == "There is no description"):
			return ""
		else:
			return self._context.get('phonecall').get('description')
		
		
	description = fields.Text('Description', default = _default_description)

	@api.multi
	def save(self):
		phonecall = self.env['crm.phonecall'].browse(self._context.get('phonecall').get('id'))
		phonecall.description = self.description
		print(phonecall.description)
		return {}

