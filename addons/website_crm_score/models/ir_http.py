from openerp.http import request
from openerp import fields, models


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    # @api.model
    def _dispatch(self):
        response = super(ir_http, self)._dispatch()

        if response.status_code == 200:

            if request.endpoint.routing.get('track', False):
                cr, uid, context = request.cr, request.uid, request.context
                lead_id = request.registry["crm.lead"].decode(request)
                url = request.httprequest.url
                date = fields.Datetime.now()
                vals = {'lead_id': lead_id, 'partner_id': request.session.get('uid', None), 'url': url}
                if not request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context):
                    # create_pageview was successful
                    pass
                else:
                    response.delete_cookie('lead_id')
                    request.session.setdefault('pages_viewed', {})[url] = date

        return response
