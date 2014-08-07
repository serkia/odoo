from openerp.osv import osv
from openerp import api, models, fields, addons, http
from openerp.http import request


class PageController(addons.website.controllers.main.Website):

    @http.route(auth="public", website=True)
    def page(self, page, **opt):

        response = super(PageController, self).page(page, **opt)
        lead_id = int(request.httprequest.cookies.get('lead_id'))
        view = request.website.get_template(page)
        score_id = view.score_id.id

        if score_id:
            if lead_id:
                # updating the lead with the new scores
                lead = request.registry["crm.lead"].browse(request.cr, request.uid, lead_id, context=request.context)
                current_scores = [score.id for score in lead.score_ids] # get all the scores that are already assigned to the lead
                if not score_id in current_scores:
                    request.registry["crm.lead"].write(request.cr, 1, lead_id, {'score_ids': [(4, score_id)]}, context=request.context) # add the new score to the lead

            else:
                # storing the score_id in a cookie 
                current_tags = request.httprequest.cookies.get('crm_tags')
                if current_tags:
                    tags = current_tags.split(',')
                    if not str(score_id) in tags:
                        tags.append(score_id)
                    else: 
                        tags = None # Todo: ugly, do something else
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
        lead_id = response.qcontext['_values']['lead_id']
        if lead_id: # a new lead has been created
            response.set_cookie('lead_id', str(lead_id))
            response.delete_cookie('crm_tags')
        else: 
            pass # lead_id == None because no lead was created
        return response


    def create_lead(self, request, values, kwargs):

        lead_id = int(request.httprequest.cookies.get('lead_id'))
        if lead_id:
            # a lead_id cookie exists, linking the information to the right lead
            lead = request.registry["crm.lead"].browse(request.cr, request.uid, lead_id, context=request.context)
            print "lead already exists", lead_id
            print values
            for fieldname, fieldvalue in values.items():
                if fieldname in lead._all_columns and not lead[fieldname]:
                    lead[fieldname] = fieldvalue
                    # TODO: what to do, merge/replace ?
        else:
            # no lead_id cookie, a lead is created
            new_lead_id = super(ContactController, self).create_lead(request, values, kwargs)
            crm_tags = request.httprequest.cookies.get('crm_tags')
            if crm_tags:
                tags = crm_tags.split(',')
                wlist = [(4, int(sid)) for sid in tags]
                request.registry["crm.lead"].write(request.cr, 1, new_lead_id, {'score_ids': wlist}, context=request.context)
            return new_lead_id
