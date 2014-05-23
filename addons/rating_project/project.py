# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp.osv import fields, osv

class Task(osv.Model):
    _name = 'project.task'
    _inherit = ['project.task','rating.model']

class Project(osv.Model):
    _inherit = "project.project"

    def action_rating(self, cr, uid, ids, context=None):
        context = dict(context or {})
        mod_obj = self.pool['ir.model.data']
        model, action_id = mod_obj.get_object_reference(cr, uid, 'rating', 'action_view_rating')
        action = self.pool['ir.actions.act_window'].read(cr, uid, action_id, context=context)
        task_ids = self.pool['project.task'].search(cr, uid, [('project_id', 'in', ids)])
        return dict(action , domain = [('res_id', 'in', task_ids), ('res_model', '=', 'project.task')])
