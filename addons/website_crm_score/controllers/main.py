from openerp import addons, http, SUPERUSER_ID, fields
from openerp.http import request


class PageController(addons.website.controllers.main.Website):

    @http.route('/page/<page:page>', auth="public", website=True)
    def page(self, page, **opt):
        response = super(PageController, self).page(page, **opt)
        # duplication of ir_http.py
        view = request.website.get_template(page)

        if view.track:
            cr, uid, context = request.cr, request.uid, request.context
            lead_id = request.registry["crm.lead"].decode(request)
            url = request.httprequest.url
            date = fields.Datetime.now()
            vals = {'lead_id': lead_id, 'partner_id': request.session.get('uid', None), 'url': url}

            if request.registry['website.crm.pageview'].create_pageview(cr, uid, vals, context=context):
                # create_pageview was successful
                pass
            else:
                response.delete_cookie('lead_id')
                request.session.setdefault('pages_viewed', {})[url] = date

        return response


class ContactController(addons.website_crm.controllers.main.contactus):

    @http.route(['/crm/contactus'], type='http', auth="public", website=True)
    def contactus(self, **kwargs):
        response = super(ContactController, self).contactus(**kwargs)
        # the cookie is written here because the response is not available in the create_lead function
        if '_values' in response.qcontext:  # contactus error : fields validation not passed
            lead_id = response.qcontext.get('_values').get('lead_id')
            if lead_id:  # a new lead has been created
                lead_model = request.registry['crm.lead']
                # sign the lead_id
                sign = lead_model.encode(lead_id)
                response.set_cookie('lead_id', sign, max_age=365 * 24 * 60 * 60)  # valid for 1 year
            else:
                pass  # lead_id == None because no lead was created
        return response

    def create_lead(self, request, values, kwargs):
        cr, uid, context = request.cr, request.uid, request.context

        create_new_lead = False
        lead_model = request.registry["crm.lead"]
        lead_id = lead_model.decode(request)

        # NOT [ (proba = 0 OR proba = 100) AND fold AND seq > 1 ]
        # modified to
        # proba != 0 AND proba != 100 OR !fold OR seq <= 1
        # the condition on the lead_id is prepended
        domain = [('id', '=', lead_id),
                  '|', '&', ('stage_id.probability', '!=', 0.0), ('stage_id.probability', '!=', 100.0),
                       '|', ('stage_id.fold', '!=', True), ('stage_id.sequence', '<=', 1)]
        lead_instance = lead_model.search(cr, SUPERUSER_ID, domain, context=context)

        if lead_instance:
            # a lead_id cookie exists and it has not been altered and the lead is not closed
            lead = lead_model.browse(cr, SUPERUSER_ID, lead_id, context=context)
            # print "desc", lead["description"]
            for fieldname, fieldvalue in values.items():
                pass
                # TODO, FIXME : broken for now, should be dealt with when the form works as planned
                # if fieldname in lead._all_columns and fieldvalue: # and not lead[fieldname]:  # rem : why this last condition ?
                #     print "leafi", fieldname, 'and',  lead[fieldname]
                #     lead[fieldname] = fieldvalue
                #     # todo: what to do, merge/replace ? pas ecraser, mais poster un message pour dire les nouveaux champs

        else:
            # either no lead_id cookie OR the lead_id doesn't exist in db OR the current one is closed -> a lead is created

            # adding the language to the lead
            lang = context.get('lang', False)
            lang_id = request.registry["res.lang"].search(cr, SUPERUSER_ID, [('code', '=', lang)], context=context)[0]
            values['lang_id'] = lang_id
            body = None
            # checking if the session user saw pages before the creation of the lead and adding them to values for lead creation
            if 'pages_viewed' in request.session:
                score_pageview_ids = []
                url_list = []
                pages_viewed = request.session['pages_viewed']
                for url, date in pages_viewed.iteritems():
                    vals = {'partner_id': request.session.get('uid', None), 'url': url, 'create_date': date}
                    score_pageview_ids.append((0, 0, vals))
                    url_list.append(url)
                del request.session['pages_viewed']
                values['score_pageview_ids'] = score_pageview_ids
                # message informing of all the pages that were seen
                urls = '</b>,<br/><b>'.join(url_list)
                body = 'The user visited <br/><b>' + urls + '</b>'

            new_lead_id = super(ContactController, self).create_lead(request, values, kwargs)

            # if pages were seen, a message is posted
            if body:
                request.registry['crm.lead'].message_post(cr, SUPERUSER_ID, [new_lead_id], body=body, subject="Pages visited", context=context)

            # ecrire le cookie ici et ne pas overrider l'autre controller
            # comment ecrire le cookie ici car response pas disponible donc pas possible de set_cookie

            return new_lead_id
