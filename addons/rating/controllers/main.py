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

import werkzeug
from openerp.addons.web.http import request
from openerp.addons.web.controllers.main import login_redirect
from openerp.addons.web import http

class Rating(http.Controller):

    @http.route(['/rating/<model>/<int:id>/<state>',
        '/rating/<model>/<int:id>/<state>'
    ], type='http', auth="public")
    def rating(self, model, id ,action=None, state=None, url=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        if not request.session.uid:
            return login_redirect()
        rating = request.registry['rating.rating']
        rating_ids = rating.search(cr, uid, [('res_model','=',model),('res_id', '=', id),('user_id', '=', uid)], context=context)
        Model = request.registry[model]
        if rating_ids:
            rating.write(cr, uid, rating_ids, {'state':state}, context=context)
        else:
            rating.create(cr, uid,  {'res_model': model, 'state':state, 'res_id': id, 'user_id': uid}, context=context)
        Model.write(cr, uid , [id] , {'is_rated': True})
        return werkzeug.utils.redirect(url and str(url) or '/web#model=%s&id=%s&view_type=form' % (model , id))

    @http.route('/survey/start/<model("survey.survey"):survey>/<model>/<int:id>',
        type='http', auth='public', website=True)
    def rating_survey(self, survey, model=None, id=None, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Model = request.registry[model]
        survey_obj = request.registry['survey.survey']
        user_input_obj = request.registry['survey.user_input']
        model_rec = Model.browse(cr, uid, id, context=context)
        if not model_rec.rating_survey_id:
            response_id = user_input_obj.create(cr, uid, {'survey_id': survey.id}, context=context)
            Model.write(cr, uid, id, {'rating_survey_id': response_id}, context=context)
        else:
            response_id = model_rec.rating_survey_id.id
        user_input = user_input_obj.browse(cr, uid, [response_id], context=context)[0]
        # Select the right page
        if user_input.state in ['new','done']:  # Intro page
            data = {'survey': survey, 'page': None, 'token': user_input.token}
            return request.website.render('survey.survey_init', data)
