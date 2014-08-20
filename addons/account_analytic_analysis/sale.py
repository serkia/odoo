# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.addons.analytic.models import analytic

class sale_order(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"
    
    contract_state = fields.Selection(analytic.ANALYTIC_ACCOUNT_STATE, string="Contract Status", compute="_compute_contract_state")
        
    @api.one
    @api.depends('project_id.state')
    def _compute_contract_state(self):
        self.contract_state = self.project_id.state or False
