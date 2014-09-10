from openerp import fields, models, modules, SUPERUSER_ID
from openerp.http import request
from psycopg2 import IntegrityError


class pageview(models.Model):
    _name = "website.crm.pageview"

    create_date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    url = fields.Char(string='Url')

    def create_pageview(self, cr, uid, vals, context=None):
        # returns True if the operation in the db was successful, False otherwise
        lead_id = vals.get('lead_id', None)
        partner_id = vals.get('partner_id', None)
        url = vals.get('url', None)
        create_date = fields.Datetime.now()

        registry = modules.registry.RegistryManager.get(request.session.db)
        with registry.cursor() as pv_cr:
            pv_cr.execute('''
                UPDATE website_crm_pageview SET create_date=%s WHERE lead_id=%s AND url=%s RETURNING id;
                ''', (create_date, lead_id, url))
            fetch = pv_cr.fetchone()
            if fetch:
                # update is successful
                return True
            else:
                # update failed
                # creating a pageview is then tried
                try:
                    # TODO: is the NOT EXIST useful ? if the row existed, it would have been updated...
                    pv_cr.execute('''
                        INSERT INTO website_crm_pageview (lead_id, partner_id, url, create_date)
                        SELECT %s,%s,%s,%s
                        WHERE NOT EXISTS (SELECT * FROM website_crm_pageview WHERE lead_id=%s AND url=%s)
                        RETURNING id;
                        ''', (lead_id, partner_id, url, create_date, lead_id, url))
                    fetch = pv_cr.fetchone()
                    if fetch:
                        # a new pageview has been created, a message is posted
                        body = '<a href="' + url + '" target="_blank"><b>' + url + '</b></a>'
                        request.registry['crm.lead'].message_post(cr, SUPERUSER_ID, [lead_id], body=body, subject="Page visited", context=context)
                        return True
                except IntegrityError:
                    # TODO: how to know if it is a lead_id error of partner_id error ?
                    return False
