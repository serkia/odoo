from openerp.osv import osv
from openerp import api, models, fields, addons, http
from openerp.http import request


class PageController(addons.website.controllers.main.Website):

    @http.route(auth="public", website=True)
    def page(self, page, **opt):

        # print 'PageController.page'

        response = super(PageController, self).page(page, **opt)
        lead_id = request.httprequest.cookies.get('lead_id')
        view = request.website.get_template(page)
        score_id = view.score_id.id

        if score_id:

            if lead_id:
                # QUESTION : Comment ajouter un score id au crm.lead ? je dois l'ajouter a score_ids
                lead = request.registry["crm.lead"].browse(request.cr, request.uid, 46, context=request.context)

            else:
                current_tags = request.httprequest.cookies.get('crm_tags')
                if current_tags:
                    tags = current_tags.split(',')
                    if not str(score_id) in tags:
                        tags.append(score_id)
                    else: 
                        tags = None # Todo: c'est moche, faire autrement
                else: 
                    tags = [score_id]

                if tags:
                    crm_tags = ','.join(map(str, tags))
                    response.set_cookie('crm_tags', crm_tags)
        return response


class ContactController(addons.website_crm.controllers.main.contactus):

    @http.route(['/page/website.contactus', '/page/contactus'], type='http', auth="public", website=True)
    def contact(self, **kwargs):

        # print 'ContactController.contactus'

        response = super(ContactController, self).contact(**kwargs)
        lead_id = request.httprequest.cookies.get('lead_id')

        if not lead_id:
            response.set_cookie('lead_id', '1') #changer la valeur
            pass
            # QUESTION : Comment recuperer le lead_id qui a ete cree dans super().contact() ?
            # QUESTION : Comment supprimer le cookie crm_tags

        else:
            # Update the information of the lead (to be done here ?)
            pass

        return response
