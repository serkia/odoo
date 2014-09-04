from openerp.http import request
from openerp import fields, models


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    # @api.model
    def _dispatch(self):
        response = super(ir_http, self)._dispatch()

        if response.status_code == 200:  # may not be needed because find_handler not used anymore

            if request.endpoint.routing.get('track', False):
                cr, uid, context = request.cr, request.uid, request.context
                lead_id = request.registry["crm.lead"].decode(request)
                url = request.httprequest.url
                date = fields.Datetime.now()
                vals = {'lead_id': lead_id, 'partner_id': request.session.get('uid', None), 'url': url}
                if lead_id and request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context):
                    # create_pageview was successful
                    pass
                else:
                    # create_pageview failed, the lead_id cookie is deleted and the tracking us done in the session
                    response.delete_cookie('lead_id')
                    # the following line doesn't work is pages_viewed already exists
                    # request.session.setdefault('pages_viewed', {})[url] = date

                    # the following works
                    if 'pages_viewed' in request.session:
                        pages_viewed = request.session['pages_viewed']
                        if not url in pages_viewed.keys():
                            pages_viewed.update({url: date})
                            request.session['pages_viewed'] = pages_viewed
                        else:
                            pages_viewed[url] = date
                            request.session['pages_viewed'] = pages_viewed
                    else:
                        request.session['pages_viewed'] = {url: date}

        return response
