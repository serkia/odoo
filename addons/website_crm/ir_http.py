# -*- coding: utf-8 -*-
from openerp.http import request
from openerp.osv import orm


class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        for key in ['campaign', 'channel', 'source']:
            var = "utm_%s" % key
            if var in request.params and var not in request.session:
                request.session[var] = request.params[var]
        return super(ir_http, self)._dispatch()
