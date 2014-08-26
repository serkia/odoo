from openerp import addons, http, SUPERUSER_ID, fields
from openerp.http import request


# def write_score(cr, uid, score_id, lead_id, model, context=None):
#     # add the new score to the lead
#     model.write(cr, SUPERUSER_ID, lead_id, {'score_ids': [(4, score_id)]}, context=context)
#     # write the date in the relational table
#     domain = [('lead_id', '=', lead_id), ('score_id', '=', score_id)]
#     ids = request.registry['crm_lead_score_date'].search(cr, SUPERUSER_ID, domain, context=context)
#     request.registry['crm_lead_score_date'].write(cr, SUPERUSER_ID, ids, {'date': fields.Datetime.now()}, context=context)
#     # writing a note in the log of the lead
#     name = request.registry['website.crm.score'].read(cr, SUPERUSER_ID, score_id, fields=['name'], context=context)
#     body = 'This lead was granted the score <b>' + str(name['name']) + '</b>'
#     model.message_post(cr, uid, [lead_id], body=body, subject="Score granted", context=context)


class PageController(addons.website.controllers.main.Website):

    @http.route('/page/<page:page>', auth="public", website=True, track=True)
    def page(self, page, **opt):

        # cr, uid, context = request.cr, request.uid, request.context
        response = super(PageController, self).page(page, **opt)
        # view = request.website.get_template(page)
        # if view.track:
        #     lead_id = request.httprequest.cookies.get('lead_id')
        #     no_lead = False

        #     if lead_id:
        #         lead_id = int(lead_id)
        #         leadModel = request.registry["crm.lead"]
        #         lead_instance = leadModel.search(cr, SUPERUSER_ID, [('id', '=', lead_id)], context=context)
        #         if lead_instance:
        #             # lead_info = leadModel.read(cr, SUPERUSER_ID, lead_id, fields=['partner_id'], context=context)
        #             vals = {'lead_id': lead_id, 'partner_id': request.session.get('uid', None), 'url': request.httprequest.url}
        #             request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context)
        #             # print "pvids", leadModel.read(cr, SUPERUSER_ID, lead_id, fields=['pageview_ids'], context=context)
        #         else:
        #             # the lead_id in the cookie corresonds to nothing in the db
        #             response.delete_cookie('lead_id')
        #             no_lead = True
        #     else:
        #         no_lead = True


        #     if no_lead:
        #         view_id = view.id
        #         current_tags = request.httprequest.cookies.get('crm_tags')
        #         if current_tags:
        #             tags = current_tags.split(',')
        #             if not str(view_id) in tags:
        #                 tags.append(view_id)
        #             else:
        #                 tags = None  # Todo: ugly, do something else
        #         else:
        #             tags = [view_id]

        #         if tags:
        #             crm_tags = ','.join(map(str, tags))
        #             response.set_cookie('crm_tags', crm_tags, max_age=365 * 24 * 60 * 60)  # valid for 1 year

        return response


class ContactController(addons.website_crm.controllers.main.contactus):

    @http.route(['/crm/contactus'], type='http', auth="public", website=True)
    def contactus(self, **kwargs):
        response = super(ContactController, self).contactus(**kwargs)
        if '_values' in response.qcontext:  # contactus error : fields validation not passed
            lead_id = response.qcontext.get('_values').get('lead_id')
            if lead_id:  # a new lead has been created
                response.set_cookie('lead_id', str(lead_id), max_age=365 * 24 * 60 * 60)  # valid for 1 year
                # response.delete_cookie('crm_tags')
            else:
                pass  # lead_id == None because no lead was created
        return response

    def create_lead(self, request, values, kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        lead_id = request.httprequest.cookies.get('lead_id')
        create_new_lead = False

        if lead_id:  # and request.registry["crm.lead"].search_read(cr, uid, [('id', '=', int(lead_id))], fields=['date_closed'], context=context)['date_closed']:
            # a lead_id cookie exists
            lead_id = int(lead_id)
            lead = request.registry["crm.lead"].browse(cr, uid, lead_id, context=context)
            if not lead['date_closed']:
                # the lead is still open
                for fieldname, fieldvalue in values.items():
                    if fieldname in lead._all_columns and not lead[fieldname]:  # rem : why this last condition ?
                        lead[fieldname] = fieldvalue
                        # TODO: what to do, merge/replace ?
            else:
                create_new_lead = True  # lead is closed
        else:
            create_new_lead = True  # no lead_id cookie

        if create_new_lead:
            print request.session
            # either no lead_id cookie or the current one is closed, a lead is created
            new_lead_id = super(ContactController, self).create_lead(request, values, kwargs)
            
            # checking if the session user saw pages before the lead creation
            if 'pages_viewed' in request.session:
                pages_viewed = request.session['pages_viewed']
                for url, date in pages_viewed.iteritems():
                    vals = {'lead_id': new_lead_id, 'partner_id': request.session.get('uid', None), 'url': url, 'create_date': date} 
                    print "pv"
                    request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context)
                del request.session['pages_viewed']

            lang = context.get('lang', False)
            lang_id = request.registry["res.lang"].search(cr, SUPERUSER_ID, [('code', '=', lang)], context=context)[0]
            request.registry["crm.lead"].write(cr, SUPERUSER_ID, new_lead_id, {'language': lang_id}, context=context)
            return new_lead_id

            # crm_tags = request.httprequest.cookies.get('crm_tags')

            # # import pdb; pdb.set_trace()
            # if crm_tags:
            #     for view_id in map(int, crm_tags.split(',')):            
            #         vals = {'lead_id': create_new_lead, 'partner_id': request.session.get('uid', None), 'view_id': view_id}
            #         request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context)
            #         # check if the pageview_id exists
            #         # pageview_instance = request.registry["website.crm.pageview"].search(cr, SUPERUSER_ID, [('id', '=', pageview_id)], context=context)
            #         # if pageview_instance:
            #         #     request.registry["website.crm.pageview"].write(cr, SUPERUSER_ID, pageview_id, {'lead_id': new_lead_id}, context=context)
                
            #     # for pageview_id in map(int, crm_tags.split(',')):
            #     #     # check if the pageview_id exists
            #     #     pageview_instance = request.registry["website.crm.pageview"].search(cr, SUPERUSER_ID, [('id', '=', pageview_id)], context=context)
            #     #     if pageview_instance:
            #     #         request.registry["website.crm.pageview"].write(cr, SUPERUSER_ID, pageview_id, {'lead_id': new_lead_id}, context=context)
            
            # lang = context.get('lang', False)
            # # NEW: il y a la langue sur request
            # lang_id = request.registry["res.lang"].search(cr, SUPERUSER_ID, [('code', '=', lang)], context=context)[0]
            # request.registry["crm.lead"].write(cr, SUPERUSER_ID, new_lead_id, {'language': lang_id}, context=context)
            # return new_lead_id
