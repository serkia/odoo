import logging
from urllib2 import Request, URLError, HTTPError

from openerp.osv import fields, osv
from openerp.tools.translate import _

HTTP_RAISE_DESC = _('HTTP Error Something is mis-configured!')
URL_RAISE = _('Internet connection refused')
URL_RAISE_DESC = _('We failed to reach a twitter server.')
OTHER_RAISE = _('Twitter authorization error!')
OTHER_RAISE_DESC = _('Please double-check your Twitter API Key and Secret!')

TWITTER_EXCEPTION = {
    304 : _('There was no new data to return.'),
    400 : _('The request was invalid or cannot be otherwise served. Requests without authentication are considered invalid and will yield this response.'),
    401 : _('Authentication credentials were missing or incorrect (May be Screen name tweets are protected!).'),
    403 : _('The request is understood, but it has been refused or access is not allowed. (Check your Twitter API Key and Secret).'),
    429 : _('Request cannot be served due to the applications rate limit having been exhausted for the resource.'),
    500 : _('Something is broken. Please post to issue to a developer forums so the Twitter team can investigate.'),
    502 : _('Twitter is down or being upgraded.'),
    503 : _('The Twitter servers are up, but overloaded with requests. Try again later.'),
    504 : _('The Twitter servers are up, but the request could not be serviced due to some failure within our stack. Try again later.')
}

_logger = logging.getLogger(__name__)

class twitter_config_settings(osv.osv_memory):
    _inherit = 'website.config.settings'

    _columns = {
         'twitter_api_key': fields.related(
                'website_id', 'twitter_api_key', type="char",
                string='Twitter API Key',
                help="Twitter API key you can get it from https://apps.twitter.com/app/new"),
         'twitter_api_secret': fields.related(
                'website_id', 'twitter_api_secret', type="char",
                string='Twitter API secret',
                help="Twitter API secret you can get it from https://apps.twitter.com/app/new"),
         'twitter_tutorial': fields.dummy(
                type="boolean", string="Show me how to obtain the Twitter API Key and Secret"),
         'twitter_screen_name': fields.related(
                'website_id', 'twitter_screen_name',
                type="char", string='Get favorites from this screen name',
                help="Screen Name of the Twitter Account from which you want to load favorites."
                "It does not have to match the API Key/Secret."),
    }
    
    def _check_twitter_authorization(self, cr, uid, config_id, context=None):
        website_obj = self.pool['website']
        website_config = self.browse(cr, uid, config_id, context=context)
        try:
            website_obj.fetch_favorite_tweets(cr, uid, [website_config.website_id.id], context=context)
        except HTTPError, e:
            _logger.warning("%s - %s" % (e.code or None, e.reason or None), exc_info=True)
            if e.code in TWITTER_EXCEPTION:
                raise osv.except_osv(_("%s - %s" % (e.code, e.reason)), TWITTER_EXCEPTION[e.code])
            else:
                _logger.warning(HTTP_RAISE_DESC, exc_info=True)
                raise osv.except_osv(_("%s - %s" % (e.code or None, e.reason or None)), HTTP_RAISE_DESC)
        except URLError, e:
            _logger.warning(URL_RAISE_DESC, exc_info=True)
            raise osv.except_osv(URL_RAISE, URL_RAISE_DESC)
        except Exception, e:
            _logger.warning(OTHER_RAISE_DESC, exc_info=True)
            raise osv.except_osv(OTHER_RAISE, OTHER_RAISE_DESC)

    def create(self, cr, uid, vals, context=None):
        res_id = super(twitter_config_settings, self).create(cr, uid, vals, context=context)
        if vals.get('twitter_api_key') and vals.get('twitter_api_secret'):
            self._check_twitter_authorization(cr, uid, res_id, context=context)
        return res_id