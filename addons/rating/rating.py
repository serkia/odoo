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


class Rating(osv.Model):
    _name = "rating.rating"

    _columns = {
        'name': fields.char('Resource Name'),
        'res_model': fields.char('Resource Model'),
        'res_id': fields.integer('Resource ID'),
        'user_id' : fields.many2one('res.users', 'Rated User'),
        'state': fields.selection([('great', 'Great'),('okay', 'Okay'),('bad', 'Not Good')], 'Select Rate', required=False),
        'response_id': fields.many2one('survey.user_input', "Response"),
    }
    
class RatingModel(osv.AbstractModel):
    _name = 'rating.model'

    def _state(self, cr, uid, ids, name, args, context=None):
        res = {}
        for rec in self.browse(cr, uid, ids, context=context):
            rating = self.pool.get('rating.rating').search_read(cr, uid, [('res_model','=',self._name),('res_id', '=', rec.id)] , ['state'], context=context)
            res[rec.id] = rating and rating[0]['state'] or ''
        return res

    _columns = {
        'rating_state': fields.function(_state, string='Rating State', type='char'),
        'is_rated': fields.boolean('Is Rated'),
        'is_rating_published': fields.boolean('Is Rating Publihsed'),
        'rating_survey_id': fields.many2one('survey.survey', "Survey")
    }

    _defaults = {
        'rating_survey_id' : 1
    }
    def send_request(self, cr, uid, ids, context=None):
        context = dict(context or {})
        data_pool = self.pool['ir.model.data']
        template_pool = self.pool['email.template']
        mail_pool = self.pool['mail.mail']
        res = False
        Model_obj = self.browse(cr, uid, ids[0],context)
        dummy, template_id = data_pool.get_object_reference(cr, uid, self._module, context['template'])
        mail_id = template_pool.send_mail(cr, uid, template_id, Model_obj.id, context=dict(context, survey=2))
        if mail_id:
            res = mail_pool.send(cr, uid, [mail_id], context=context)
        return res
            
    def published(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_rating_published': True}, context=context)

    def unpublished(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_rating_published': False}, context=context)

    def action_print_survey(self, cr, uid, ids, context=None):
        """ If response is available then print this response otherwise print survey form (print template of the survey) """
        context = context if context else {}
        rec = self.browse(cr, uid, ids, context=context)[0]
        survey_obj = self.pool.get('survey.survey')
        response_obj = self.pool.get('survey.user_input')
        if rec.rating_survey_id.id:
            response = response_obj.browse(cr, uid, rec.rating_survey_id.id, context=context)
            context.update({'survey_token': response.token})
        return survey_obj.action_print_survey(cr, uid, [rec.rating_survey_id.id], context=context)

