# -*- coding: utf-8 -*-

import werkzeug
from openerp import http, _
from openerp.http import request


class Rating(http.Controller):

    @http.route('/rating/<token>', type='http', auth="public")
    def rating(self, token=None, state=None, **post):
        rating_obj = request.env['rating.rating']
        if token and state:
            record = getattr(rating_obj, 'do_%s' % state)(token=token)
            if record and not request.session.uid:
                return request.render('rating.rating_view', {'value': record, 'state': state})
            elif record:
                return werkzeug.utils.redirect('/web#model=%s&id=%s&view_type=form' % (record._name, record.id))
        return request.render("rating.403")
