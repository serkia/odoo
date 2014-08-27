from openerp import fields, models, SUPERUSER_ID, modules
from openerp.http import request


class pageview(models.Model):
    _name = "website.crm.pageview"

    create_date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    url = fields.Char(string='Url')

    def create_pageview(self, cr, uid, vals, context=None, new_cursor=False):
        lead_id = vals.get('lead_id', None)
        partner_id = vals.get('partner_id', None)
        url = vals.get('url', None)
        create_date = fields.Datetime.now()

        pv_cr = cr
        if new_cursor:
            # another cursor is needed to avoid the rollback in the case
            # of a page of the website triggering this creation
            registry = modules.registry.RegistryManager.get(request.session.db)
            pv_cr = registry.cursor()

        pv_cr.execute('''INSERT INTO website_crm_pageview (lead_id, partner_id, url, create_date)
            SELECT %s,%s,%s,%s
            WHERE NOT EXISTS (SELECT * FROM website_crm_pageview WHERE lead_id=%s AND url=%s)
            RETURNING id;
            ''', (lead_id, partner_id, url, create_date, lead_id, url))

        fetch = pv_cr.fetchone()
        if fetch:
            body = 'The user visited <br><b>' + url + '</b> <br>on ' + create_date
            request.registry['crm.lead'].message_post(cr, SUPERUSER_ID, [lead_id], body=body, subject="Page visited", context=context)

        if new_cursor:
            pv_cr.commit()
            pv_cr.close()
