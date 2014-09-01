from openerp import fields, models, SUPERUSER_ID, modules
from openerp.http import request


class pageview(models.Model):
    _name = "website.crm.pageview"

    create_date = fields.Datetime(string='Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    url = fields.Char(string='Url')

    def create_pageview(self, cr, uid, vals, context=None):
        lead_id = vals.get('lead_id', None)
        partner_id = vals.get('partner_id', None)
        url = vals.get('url', None)
        create_date = fields.Datetime.now()

        registry = modules.registry.RegistryManager.get(request.session.db)
        with registry.cursor() as pv_cr:
            pv_cr.execute('''INSERT INTO website_crm_pageview (lead_id, partner_id, url, create_date)
                SELECT %s,%s,%s,%s
                WHERE NOT EXISTS (SELECT * FROM website_crm_pageview WHERE lead_id=%s AND url=%s)
                RETURNING id;
                ''', (lead_id, partner_id, url, create_date, lead_id, url))

            fetch = pv_cr.fetchone()
            if fetch:
                body = 'The user visited <br><b>' + url + '</b> <br>on ' + create_date
                request.registry['crm.lead'].message_post(cr, SUPERUSER_ID, [lead_id], body=body, subject="Page visited", context=context) 
            pv_cr.commit()



        # pv_cr = cr
        # if new_cursor:
        #     # another cursor is needed to avoid the rollback in the case
        #     # of a page of the website triggering this creation
        #     registry = modules.registry.RegistryManager.get(request.session.db)
        #     pv_cr = registry.cursor()

        # # lead value = {
        # #     name...
        # #     score_pageview_ids = [
        # #             (0, 0, {'url': http..., 'date': date})
        # #         ]

        # # }
        # # # creer un seul message quand le elad est cree pour dire les pages qui ont ete vue

        # # env['crm lead '].create(lead values)

        # # todo: si le lead id n'est pas bon, catch l'erreur de db car dans un nouveau cursor...
        # # update where, si nb d'entrees changees = 0, alors create
        # # cr.row_count pour savoir le nombre de row changees

        # # partner id est inconnu mtnt, donc, dans selsect le deuxieme %s : select partner_id from res_user where id = uid (passe en argument))
        # pv_cr.execute('''INSERT INTO website_crm_pageview (lead_id, partner_id, url, create_date)
        #     SELECT %s,%s,%s,%s
        #     WHERE NOT EXISTS (SELECT * FROM website_crm_pageview WHERE lead_id=%s AND url=%s)
        #     RETURNING id;
        #     ''', (lead_id, partner_id, url, create_date, lead_id, url))

        # fetch = pv_cr.fetchone()
        # if fetch:
        #     body = 'The user visited <br><b>' + url + '</b> <br>on ' + create_date
        #     request.registry['crm.lead'].message_post(cr, SUPERUSER_ID, [lead_id], body=body, subject="Page visited", context=context)

        # if new_cursor:
        #     pv_cr.commit()
        #     pv_cr.close()
