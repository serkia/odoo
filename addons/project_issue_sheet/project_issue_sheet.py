 #-*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields,osv,orm
from openerp.tools.translate import _
from openerp.addons.analytic.models import analytic

class project_issue(osv.osv):
    _inherit = 'project.issue'
    _description = 'project issue'
    
    def _get_current_contract_state(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for issue in self.browse(cr, uid, ids, context=context):
            res[issue.id] = False
            contrat = issue.project_id and issue.project_id.analytic_account_id
            if contrat.partner_id and contrat.use_issues:
                res[issue.id] = contrat.state
        return res
        
    _columns = {
        'timesheet_ids': fields.one2many('hr.analytic.timesheet', 'issue_id', 'Timesheets'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'), 
        'contract_state': fields.function(_get_current_contract_state, string='Contract Status', type='selection', selection=analytic.ANALYTIC_ACCOUNT_STATE), 
    }
    
    def on_change_project(self, cr, uid, ids, project_id, context=None):
        if not project_id:
            return {}

        result = super(project_issue, self).on_change_project(cr, uid, ids, project_id, context=context)
        
        project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)
        if 'value' not in result:
            result['value'] = {}

        account = project.analytic_account_id
        if account:
            result['value']['analytic_account_id'] = account.id
            result['value']['contract_state'] = account.partner_id and account.use_issues and account.state or False

        return result

    def on_change_account_id(self, cr, uid, ids, account_id, context=None):
        if not account_id:
            return {}

        account = self.pool.get('account.analytic.account').browse(cr, uid, account_id, context=context)
        result = {}

        if account and account.state == 'pending':
            result = {'warning' : {'title' : _('Analytic Account'), 'message' : _('The Analytic Account is pending !')}}
            
        return result


class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    _description = 'account analytic line'
    _columns = {
        'create_date' : fields.datetime('Create Date', readonly=True),
    }


class hr_analytic_issue(osv.osv):

    _inherit = 'hr.analytic.timesheet'
    _description = 'hr analytic timesheet'
    _columns = {
        'issue_id' : fields.many2one('project.issue', 'Issue'),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
