import openerp
from openerp import tools
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website_forum.controllers.main import WebsiteForum as controllers

class WebsiteForumSEO(controllers):
    
    # Post
    # --------------------------------------------------
    @http.route(['/forum/<model("forum.forum"):forum>/<post_type>/new',
                 '/forum/<model("forum.forum"):forum>/<model("forum.post"):post_parent>/reply']
                , type='http', auth="user", methods=['POST'], website=True)
    def post_create(self, forum, post_parent='', post_type='', **post):
        post.update({'content' : request.env['forum.seo'].update_seo_word(post.get('content'))})
        return super(WebsiteForumSEO, self).post_create(forum=forum, post_parent=post_parent, post_type=post_type, **post)
    
    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/save', type='http', auth="user", methods=['POST'], website=True)
    def post_save(self, forum, post, **kwargs):
        kwargs.update({'content' : request.env['forum.seo'].update_seo_word(kwargs.get('content'))})
        return super(WebsiteForumSEO, self).post_save(forum=forum, post=post, **kwargs)
