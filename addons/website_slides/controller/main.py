# -*- coding: utf-8 -*-

import werkzeug
import simplejson

from openerp import SUPERUSER_ID
from openerp.http import request
from openerp.addons.web import http
from openerp.tools.translate import _


class main(http.Controller):

    _slides_per_page = 12
    _slides_per_list = 20

    @http.route('/slides/editmessage/<model("slide.channel"):channel>', type='http', auth="user", website=True)
    def edit_error_message(self, channel):
        values = {
            'channel':channel
        }
        return request.website.render('website_slides.privatedit', values)

    @http.route('/slides', type='http', auth="public", website=True)
    def index(self, *args, **post):
        '''
        return list of channels if more then one channel is available
        else redirect to slides of first channel 
        '''
        channel_obj = request.env['slide.channel']
        user = request.env.user
        domain = []

        if user.id == request.website.user_id.id:
            domain += [('website_published','=', True), ('visibility','!=','private')]

        if user.id not in (request.website.user_id.id, SUPERUSER_ID):
            domain += [('website_published','=', True)]

        channels = channel_obj.search(domain, order='sequence')

        if len(channels) <= 1:
            return request.redirect("/slides/%s" % channels.id)

        vals = {
            'channels': channels,
            'user': user,
            'is_public_user': user.id == request.website.user_id.id
        }
        return request.website.render('website_slides.channels', vals)

    @http.route(['/slides/<model("slide.channel"):channel>',
                '/slides/<model("slide.channel"):channel>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/<types>',
                '/slides/<model("slide.channel"):channel>/<types>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/tag/<tags>',
                '/slides/<model("slide.channel"):channel>/tag/<tags>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/category/<model("slide.category"):category>',
                '/slides/<model("slide.channel"):channel>/category/<model("slide.category"):category>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/category/<model("slide.category"):category>/<types>',
                '/slides/<model("slide.channel"):channel>/category/<model("slide.category"):category>/<types>/page/<int:page>',
                ], type='http', auth="public", website=True)
    def slides(self, channel=0, category=0, page=1, types='', tags='', sorting='creation'):
        user = request.env.user
        slide_obj = request.env['slide.slide']
        category_obj = request.env['slide.category']

        domain = [('channel_id','=',channel.id)]

        slides = []
        famous = None

        if request.env.user.id == request.website.user_id.id:
            domain += [('website_published', '=', True)]

        if tags:
            domain += [('tag_ids.name', '=', tags)]

        values = {
            'tags':tags,
            'channel': channel,
            'user': user,
            'is_public_user': user.id == request.website.user_id.id
        }

        if types:
            domain += [('slide_type', '=', types)]

        if category:
            domain += [('category_id', '=', category.id)]

        if sorting == 'date':
            order = 'date_publish desc'
        elif sorting == 'view':
            order = 'total_views desc'
        elif sorting == 'vote':
            order = 'likes desc'
        else:
            sorting = 'date'
            order = 'date_publish desc'

        url = "/slides/%s" % (channel.id)
        if tags:
            url = "/slides/%s/tag/%s" % (channel.id, tags)

        if types:
            url = "/slides/%s/%s" % (channel.id, types)

        if category:
            url = "/slides/%s/category/%s" % (channel.id, category.id)

        if category and types:
            url = "/slides/%s/category/%s/%s" % (channel.id, category.id, types)

        url_args = {}
        if sorting:
            url_args['sorting'] = sorting

        pager_count = slide_obj.search_count(domain)
        pager = request.website.pager(url=url, total=pager_count, page=page,
                                      step=self._slides_per_page, scope=self._slides_per_page,
                                      url_args=url_args)

        slides = slide_obj.search(domain, limit=self._slides_per_page, offset=pager['offset'], order=order)
        famous = channel.get_promoted_slide()
        values.update({
            'slides': slides,
            'all_count': pager_count,
            'pager': pager,
            'types': types,
            'sorting': sorting,
            'category': category,
            'famous': famous
        })

        if not types and not category:
            category_ids = category_obj.search([('channel_id','=',channel.id)])
            category_datas = {}
            for category_id in category_ids:
                result = category_id.get_slides_by_category(domain, 4, order)
                category_datas.update({
                    category_id.name:result
                })

            values.update({
                'category_datas':category_datas,
                'category_ids':category_ids,
            })

        return request.website.render('website_slides.home', values)

    def getslide(self, channel, slide, types='', sorting='', search='', tags=''):
        user = request.env.user
        most_viewed_ids = slide.get_most_viewed_slides(self._slides_per_list)
        related_ids = slide.sudo().get_related_slides(self._slides_per_list)

        comments = slide.website_message_ids

        values = {
            'most_viewed_ids':most_viewed_ids,
            'relatedslides': related_ids,
            'channel': slide.channel_id,
            'user':user,
            'types':types,
            'is_public_user': user.id == request.website.user_id.id,
            'is_super_user': user.id == user.sudo().id,
            'private':True,
            'slide_id':slide.id,
            'type':slide.slide_type,
            'slidename':slide.name
        }

        if slide.channel_id.visibility in ('private', 'group') and user.id != SUPERUSER_ID:
            access = False
            for group in slide.channel_id.group_ids:
                if user in group.sudo().users:
                    access = True
                    break

        if slide.channel_id.visibility == 'public' or user.id == SUPERUSER_ID:
            access = True

        if access:
            values.update({
                'slide':slide,
                'comments': comments,
                'private':False
            })

        return values

    @http.route([
                '/slides/<model("slide.channel"):channel>/<types>/<model("slide.slide"):slide>',
                '/slides/<model("slide.channel"):channel>/<types>/tag/<tags>/<model("slide.slide"):slide>'
                ], type='http', auth="public", website=True)
    def slide_view(self, channel, slide, types='', sorting='', search='', tags=''):
        values = self.getslide(channel, slide, types, sorting, search, tags)
        slide.sudo().set_viewed()
        return request.website.render('website_slides.slide_view', values)


    @http.route('/slides/content/<model("slide.slide"):slide>', type='http', auth="public", website=True)
    def slide_view_content(self, slide):
        response = werkzeug.wrappers.Response()
        response.data = slide.datas.decode('base64')
        response.mimetype = 'application/pdf'
        del response.headers['Content-Length']
        return response

    @http.route('/slides/embed/count', type='http', auth='public', website=True)
    def slides_embed_count(self, slide, url):
        request.env['slide.embed'].sudo().set_count(slide, url)


    @http.route('/slides/comment/<model("slide.slide"):slide>', type='http', auth="public", methods=['POST'], website=True)
    def slides_comment(self, slide, **post):
        slide_obj = request.env['slide.slide']
        partner_obj = request.env['res.partner']
        partner_ids = False
        message_id = False

        #TODO: make website_published False by default and write an method to send email with random back link, 
        #which will post all comments posted with that email address
        website_published = False

        if post.get('comment'):
            if request.uid != request.website.user_id.id:
                partner_ids = [request.env.user.partner_id]
                website_published = True
            else:
                partner_ids = partner_obj.sudo().search([('email','=',post.get('email'))])
                if not partner_ids or not partner_ids[0]:
                    partner_ids = [partner_obj.sudo().create({
                        'name': post.get('name'), 
                        'email': post.get('email')
                    })]

            if partner_ids:
                message_id = slide.sudo().with_context(mail_create_nosubcribe=True).message_post(
                    body=post.get('comment'),
                    type='comment',
                    subtype='mt_comment',
                    author_id=partner_ids[0].id,
                    website_published = website_published
                )

        return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")

    @http.route('/slides/<model("slide.channel"):channel>/view/<model("slide.slide"):slide>/like', type='json', auth="public", website=True)
    def slide_like(self, channel, slide, **post):
        if slide.sudo().set_like():
            return slide.likes
        return {'error': 'Error on wirte Data'}

    @http.route('/slides/<model("slide.channel"):channel>/view/<model("slide.slide"):slide>/dislike', type='json', auth="public", website=True)
    def slide_dislike(self, channel, slide, **post):
        if slide.sudo().set_dislike():
            return slide.dislikes

        return {'error': 'Error on wirte Data'}

    @http.route(['/slides/sendbymail/<model("slide.slide"):slide>'], type='json', auth='user', methods=['POST'], website=True)
    def sendbymail(self, slide, email):
        result = slide.sendemail(email)
        return result

    @http.route(['/slides/add_slide'], type='json', auth='user', methods=['POST'], website=True)
    def create_slide(self, *args, **post):
        tag_obj = request.env['slide.tag']
        slide_obj = request.env['slide.slide']

        if slide_obj.search([('name','=',post['name']),('channel_id','=',post['channel_id'])]):
            return {
                'error':_('This title already exists in the channel, rename and try again.')
            }

        tags = post.get('tag_ids')
        tag_ids = []
        for tag in tags:
            tag_id = tag_obj.search([('name', '=', tag)])
            if tag_id:
                tag_ids.append((4, tag_id[0].id))
            else:
                tag_ids.append((0, 0, {'name': tag}))
            post['tag_ids'] = tag_ids

        if request.env.user.id != 1:
            post['website_published'] = False

        slide_id = slide_obj.create(post)
        return {'url': "/slides/%s/%s/%s" % (post.get('channel_id'), post['slide_type'], slide_id.id)}

    @http.route('/slides/overlay/<model("slide.slide"):slide>', type='json', auth="public", website=True)
    def get_next_slides(self, slide):
        slides_to_suggest = 9
        suggested_ids = slide.get_related_slides(slides_to_suggest)
        if len(suggested_ids) < slides_to_suggest:
            slides_to_suggest = slides_to_suggest - len(suggested_ids)
            suggested_ids += slide.get_most_viewed_slides(slides_to_suggest)

        vals = []
        for suggest in suggested_ids:
            val = {
                'img_src':'/website/image/slide.slide/%s/image_thumb' % (suggest.id),
                'caption':suggest.name,
                'url':suggest.get_share_url()
            }
            vals.append(val)

        return vals

    @http.route('/slides/embed/<model("slide.slide"):slide>', type='http', auth='public', website=True)
    def slides_embed(self, slide, page="1"):
        values = self.getslide(channel=False, slideview=slide, types=False, sorting=False, search=False, tags=False)
        slide.sudo().set_embed_viewed()

        values.update({
            'page':page,
        })
        return request.website.render('website_slides.pdfembed', values)

    @http.route('/slides/get_tags', type='http', auth="public", methods=['GET'], website=True)
    def tag_read(self, **post):
        tags = request.env['slide.tag'].search_read([], ['name'])
        data = [tag['name'] for tag in tags]
        return simplejson.dumps(data)

    @http.route('/slides/get_category/<model("slide.channel"):channel>', type='json', auth="public", website=True)
    def get_category(self, channel):
        category_obj = request.env['slide.category']
        categories = category_obj.name_search(name='', args=[('channel_id','=',channel.id)], operator='ilike', limit=100)
        res = []
        for category in categories:
            res.append({
                'id': category[0],
                'name': category[1]
            })
        return res

    @http.route(['/slides/<model("slide.channel"):channel>/search',
                '/slides/<model("slide.channel"):channel>/search/page/<int:page>'
                ], type='http', auth="public", website=True)
    def search(self, channel=0, query=False, page=1, order=False):
        slide_obj = request.env['slide.slide']

        domain = [('channel_id','=',channel.id)]

        if request.env.user.id == request.website.user_id.id:
            domain += [('website_published', '=', True)]

        if query:
            domain += ['|', '|', ('name', 'ilike', query), ('description', 'ilike', query), ('index_content', 'ilike', query)]

        url = "/slides/%s/search" % (channel.id)
        url_args = {}
        if query:
            url_args['query'] = query

        pager_count = slide_obj.search_count(domain)
        pager = request.website.pager(url=url, total=pager_count, page=page,
                                      step=self._slides_per_page, scope=self._slides_per_page,
                                      url_args=url_args)

        slides = slide_obj.search(domain, limit=self._slides_per_page, offset=pager['offset'], order=order)

        values = {
            'channel': channel,
            'pager': pager,
            'slides': slides,
            'query': query,
            'order': order
        }
        return request.website.render('website_slides.searchresult', values)
