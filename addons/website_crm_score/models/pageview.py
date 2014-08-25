from openerp import fields, api, models, SUPERUSER_ID, modules
from openerp.http import request


class pageview(models.Model):
    _name = "website.crm.pageview"

    create_date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    url = fields.Char(string='Url')

    def create_pageview(self, cr, uid, vals, context=None):
        # todo: check that the pageview doesn't exist already
        values = {
            'lead_id': vals.get('lead_id', None),
            # todo: what use for the partner id ?
            # request.user.partner_id
            'partner_id': vals.get('partner_id', None),
            'url': vals.get('url', None),
            'create_date': fields.Datetime.now(),
        }
        # sometimes, partner_id == False
        if not values['partner_id']:
            values['partner_id'] = None
        # values['url'] = "toto"

        # domain = [('lead_id', '=', values['lead_id']),
        #           ('partner_id', '=', values['partner_id']),
        #           ('url', '=', values['url']),
        #           ]
        # pv_instance = self.search(cr, SUPERUSER_ID, domain, context=context)
        # print pv_instance

        # as the controller is public, a rollback is done,
        # for the pageview to be created, the commit must be explicit
        registry = modules.registry.RegistryManager.get(request.session.db)
        with registry.cursor() as pv_cr:
            pv_cr.execute('''INSERT INTO website_crm_pageview (lead_id, partner_id, url, create_date)
                SELECT %s,%s,%s,%s
                WHERE NOT EXISTS (SELECT * FROM website_crm_pageview WHERE lead_id=%s AND url=%s) RETURNING id;
                ''', (values['lead_id'], values['partner_id'], values['url'], values['create_date'], values['lead_id'], values['url']))
            fetch = pv_cr.fetchone()
            pageview_id = None
            if fetch:
                pageview_id = fetch[0]
                pv_cr.commit()

            print "page view", pageview_id
            # pageview_id = self.create(pv_cr, SUPERUSER_ID, values, context=context)

            return pageview_id
