from openerp.osv import osv
from openerp import api, models, fields, addons, http
from openerp.http import request


class PageController(addons.website.controllers.main.Website):

    @http.route(auth="public", website=True)
    def page(self, page, **opt):

        response = super(PageController, self).page(page, **opt)
        lead_id = request.httprequest.cookies.get('lead_id')
        view = request.website.get_template(page)
        score_id = view.score_id.id

        print "id", score_id
        if score_id
            if lead_id:
                pass
            else:
                current_tags = request.httprequest.cookies.get('crm_tags')
                if current_tags:
                    tags = current_tags.split(',')
                    if not str(score_id) in tags:
                        tags.append(score_id)
                    else: 
                        tags = None
                else: 
                    tags = [score_id]

                if tags:
                    crm_tags = ','.join(map(str, tags))
                    response.set_cookie('crm_tags', crm_tags)
        return response