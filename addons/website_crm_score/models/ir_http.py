# from openerp.osv import orm
from openerp.http import request
from openerp import api, models, SUPERUSER_ID


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    # @api.model
    def _dispatch(self):

        cr, uid, context = request.cr, request.uid, request.context
        func = None
        func, arguments = self._find_handler()
        track = func.routing.get('track', False)
        no_lead = False

        # print 'func', func.routing
        # url in request.httprequest.url
        response = super(ir_http, self)._dispatch()
        print 'url', request.httprequest.url_root
        print 'root', func.routing
        print 'paht', response.qcontext.get('path', '')
        # print 'qcontext', response.qcontext
        
        # print self.pool.get('ir.model.data').get_object_reference(cr, uid, 'website', response.qcontext['path'])[1]
        # print self.pool.get('ir.model.data').xmlid_lookup(cr, uid, response.qcontext['path'])


        # import pdb; pdb.set_trace()

        if track:
            lead_id = request.httprequest.cookies.get('lead_id')
            if lead_id:

                lead_id = int(lead_id)
                leadModel = request.registry["crm.lead"]
                lead_instance = leadModel.search(cr, SUPERUSER_ID, [('id', '=', lead_id)], context=context)
                if lead_instance:
                    lead_info = leadModel.read(cr, SUPERUSER_ID, lead_id, fields=['partner_id'], context=context)
                    vals = {'lead_id': lead_id, 'partner_id': lead_info['partner_id'], 'url': request.httprequest.url}
                    request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context)
                    # print "pvids", leadModel.read(cr, SUPERUSER_ID, lead_id, fields=['pageview_ids'], context=context)
                else:
                    # the lead_id in the cookie corresonds to nothing in the db
                    response.delete_cookie('lead_id')
                    no_lead = True
            else:
                no_lead = True

        return response