from openerp import addons, http, SUPERUSER_ID
from openerp.http import request

#def getTags(requests) ....
#    return request.httprequest.cookies.get('crm_tags','').split(,)


class PageController(addons.website.controllers.main.Website):

    @http.route(auth="public", website=True)
    def page(self, page, **opt):

        response = super(PageController, self).page(page, **opt)
        view = request.website.get_template(page)
        score_id = view and view.score_id and view.score_id.id

        if score_id:
            # Rem : move because don t need it if not score...
            lead_id = request.httprequest.cookies.get('lead_id')
            if lead_id:
                # Rem : int(None) will launch a traceback ! You was not sure that lead_id exists before it
                lead_id = int(lead_id)
                leadModel = request.registry["crm.lead"]
                # updating the lead with the new scores
                lead = leadModel.browse(request.cr, request.uid, lead_id, context=request.context)
                current_scores = [score.id for score in lead.score_ids]  # get all the scores that are already assigned to the lead
                if not score_id in current_scores:
                    leadModel.write(request.cr, SUPERUSER_ID, lead_id, {'score_ids': [(4, score_id)]}, context=request.context)  # add the new score to the lead

            else:
                # storing the score_id in a cookie
                current_tags = request.httprequest.cookies.get('crm_tags')
                if current_tags:
                    tags = current_tags.split(',')
                    if not str(score_id) in tags:
                        tags.append(score_id)
                    else:
                        tags = None  # Todo: ugly, do something else
                else:
                    tags = [score_id]

                if tags:
                    crm_tags = ','.join(map(str, tags))
                    response.set_cookie('crm_tags', crm_tags)

        return response


class ContactController(addons.website_crm.controllers.main.contactus):

    @http.route(['/crm/contactus'], type='http', auth="public", website=True)
    def contactus(self, **kwargs):
        response = super(ContactController, self).contactus(**kwargs)
        # rem: if error, you dont pass into preRenderThanks so you don't have _values...
        lead_id = response.qcontext.get('_values', {}).get('lead_id')
        if lead_id:  # a new lead has been created
            response.set_cookie('lead_id', str(lead_id))  # rem: why cats as string ? not auto for cookies?
            response.delete_cookie('crm_tags')
        else:
            pass  # lead_id == None because no lead was created
        return response

    def create_lead(self, request, values, kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        lead_id = request.httprequest.cookies.get('lead_id')
        if lead_id:
            lead_id = int(lead_id)
            # a lead_id cookie exists, linking the information to the right lead
            lead = request.registry["crm.lead"].browse(cr, uid, lead_id, context=context)
            print "lead already exists", lead_id
            print values
            for fieldname, fieldvalue in values.items():
                if fieldname in lead._all_columns and not lead[fieldname]:  # rem : why this last condition ?
                    lead[fieldname] = fieldvalue
                    # TODO: what to do, merge/replace ?
        else:
            # no lead_id cookie, a lead is created
            new_lead_id = super(ContactController, self).create_lead(request, values, kwargs)
            crm_tags = request.httprequest.cookies.get('crm_tags')
            if crm_tags:
                wlist = [(4, int(sid)) for sid in crm_tags.split(',')]
                request.registry["crm.lead"].write(cr, SUPERUSER_ID, new_lead_id, {'score_ids': wlist}, context=context)
            return new_lead_id
