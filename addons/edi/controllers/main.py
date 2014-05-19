import werkzeug.urls

import openerp
import openerp.addons.web.controllers.main as webmain

class EDI(openerp.http.Controller):

    @openerp.http.route('/edi/import_url', type='http', auth='none')
    def import_url(self, url):
        # http://hostname:8069/edi/import_url?url=URIEncodedURL
        req = openerp.http.request

        # `url` may contain a full URL with a valid query string, we basically want to watch out for XML brackets and double-quotes 
        safe_url = werkzeug.url_quote_plus(url,':/?&;=')

        return req.render('web.webclient_bootstrap', {
            'init_script': 'openerp.edi.edi_import("%s");' % safe_url
        })

    @openerp.http.route('/edi/import_edi_url', type='json', auth='none')
    def import_edi_url(self, url):
        req = openerp.http.request
        result = req.session.proxy('edi').import_edi_url(req.session._db, req.session._uid, req.session._password, url)
        if len(result) == 1:
            return {"action": webmain.clean_action(req, result[0][2])}
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
