# from openerp.osv import orm
from openerp.http import request
from openerp import fields, models, SUPERUSER_ID


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    # @api.model
    def _dispatch(self):
        response = super(ir_http, self)._dispatch()

        # first_pass = not hasattr(request, 'website')
        # if first_pass:

        # is it ok to do so ?
        if response.status_code == 200:
            cr, uid, context = request.cr, request.uid, request.context
            func, arguments = self._find_handler()

            track = func.routing.get('track', False)
            no_lead = False

            if track:
                do_track = True
                if response.qcontext and 'path' in response.qcontext:
                    # there is a view, we want to know if we have to track it
                    page = response.qcontext.get('path')
                    view = request.website.get_template(page)
                    if not view.track:
                        do_track = False

                if do_track:
                    lead_id = request.httprequest.cookies.get('lead_id')
                    no_lead = False

                    if lead_id:
                        lead_id = int(lead_id)
                        leadModel = request.registry["crm.lead"]
                        lead_instance = leadModel.search(cr, SUPERUSER_ID, [('id', '=', lead_id)], context=context)
                        if lead_instance:
                            # creation of the pageview for this page, duplication is cheched in create_pageview
                            vals = {'lead_id': lead_id, 'partner_id': request.session.get('uid', None), 'url': request.httprequest.url}
                            request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context, new_cursor=True)
                        else:
                            # the lead_id in the cookie corresonds to nothing in the db
                            response.delete_cookie('lead_id')
                            no_lead = True
                    else:
                        no_lead = True

                    if no_lead:
                        url = request.httprequest.url

                        if 'pages_viewed' in request.session:
                            # if not request.session['pages_viewed']:
                            #     del request.session['pages_viewed']
                            # else:
                            pages_viewed = request.session['pages_viewed']
                            if not url in pages_viewed.keys():
                                # No refreshing of the date
                                pages_viewed.update({url: fields.Datetime.now()})
                                request.session['pages_viewed'] = pages_viewed
                        else:
                            request.session['pages_viewed'] = {url: fields.Datetime.now()}

        return response
