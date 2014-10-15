# -*- coding: utf-8 -*-

import werkzeug
import simplejson

from openerp import SUPERUSER_ID
from openerp.http import request
from openerp.addons.web import http


class main(http.Controller):

    _slides_per_page = 12
    _slides_per_list = 20

    def _slides_message(self, user, attachment_id=0, **post):
        attachment = request.env['ir.attachment']
        partner_obj = request.env['res.partner']

        if request.uid != request.website.user_id.id:
            partner_ids = [user.partner_id.id]
        else:
            partner_ids = attachment.sudo()._find_partner_from_emails(0, [post.get('email')])
            if not partner_ids or not partner_ids[0]:
                partner_ids = [partner_obj.sudo().create({'name': post.get('name'), 'email': post.get('email')})]
        message_id = attachment.search([('id', '=', int(attachment_id))]).sudo().with_context(mail_create_nosubcribe=True).message_post(
            body=post.get('comment'),
            type='comment',
            subtype='mt_comment',
            author_id=partner_ids[0],
            path=post.get('path', False),
        )
        return message_id

    @http.route('/slides', type='http', auth="public", website=True)
    def channels(self, *args, **post):
        directory = request.env['slide.channel']
        user = request.env.user
        channels = directory.search([('website_published','=', True), ('visiblity','!=','private')], order='sequence')

        if len(channels) <= 1:
            return request.redirect("/slides/%s" % channels.id)

        vals = {
            'channels': channels,
            'user': user,
            'is_public_user': user.id == request.website.user_id.id
        }
        return request.website.render('website_slides.channels', vals)

    @http.route(['/slides/<model("slide.channel"):channel>/search',
                '/slides/<model("slide.channel"):channel>/search/page/<int:page>'
                ], type='http', auth="public", website=True)
    def search(self, channel=0, query=False, page=1, order=False):
        attachment = request.env['ir.attachment']

        domain = [('is_slide','=','True'), ('channel_id','=',channel.id)]

        if request.env.user.id == request.website.user_id.id:
            domain += [('website_published', '=', True)]

        if query:
            domain += ['|', '|', ('name', 'ilike', query), ('description', 'ilike', query), ('index_content', 'ilike', query)]

        url = "/slides/%s/search" % (channel.id)
        url_args = {}
        if query:
            url_args['query'] = query

        pager_count = attachment.search_count(domain)
        pager = request.website.pager(url=url, total=pager_count, page=page,
                                      step=self._slides_per_page, scope=self._slides_per_page,
                                      url_args=url_args)

        attachment_ids = attachment.search(domain, limit=self._slides_per_page, offset=pager['offset'], order=order)

        values = {
            'channel': channel,
            'pager': pager,
            'attachment_ids': attachment_ids,
            'query': query,
            'order': order
        }
        return request.website.render('website_slides.searchresult', values)

    @http.route(['/slides/<model("slide.channel"):channel>',
                '/slides/<model("slide.channel"):channel>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/<types>',
                '/slides/<model("slide.channel"):channel>/<types>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/tag/<tags>',
                '/slides/<model("slide.channel"):channel>/tag/<tags>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/category/<model("ir.attachment.category"):category>',
                '/slides/<model("slide.channel"):channel>/category/<model("ir.attachment.category"):category>/page/<int:page>',

                '/slides/<model("slide.channel"):channel>/category/<model("ir.attachment.category"):category>/<types>',
                '/slides/<model("slide.channel"):channel>/category/<model("ir.attachment.category"):category>/<types>/page/<int:page>',
                ], type='http', auth="public", website=True)
    def slides(self, channel=0, category=0, page=1, types='', tags='', sorting='creation'):
        user = request.env.user
        attachment = request.env['ir.attachment']
        category_pool = request.env['ir.attachment.category']

        domain = [('is_slide','=','True'), ('channel_id','=',channel.id)]

        attachment_ids = []
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
            order = 'write_date desc'
        elif sorting == 'view':
            order = 'total_views desc'
        elif sorting == 'vote':
            order = 'likes desc'
        else:
            sorting = 'date'
            order = 'write_date desc'

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

        pager_count = attachment.search_count(domain)
        pager = request.website.pager(url=url, total=pager_count, page=page,
                                      step=self._slides_per_page, scope=self._slides_per_page,
                                      url_args=url_args)

        attachment_ids = attachment.search(domain, limit=self._slides_per_page, offset=pager['offset'], order=order)
        famous = channel.get_mostviewed()
        values.update({
            'attachment_ids': attachment_ids,
            'all_count': pager_count,
            'pager': pager,
            'types': types,
            'sorting': sorting,
            'category': category,
            'famous': famous
        })

        if not types and not category:
            category_ids = category_pool.search([('channel_id','=',channel.id)])
            category_datas = {}
            for category_id in category_ids:
                result = category_id.get_slides(domain, 4, order)
                category_datas.update({
                    category_id.name:result
                })

            values.update({
                'category_datas':category_datas,
                'category_ids':category_ids,
            })

        return request.website.render('website_slides.home', values)

    def getslide(self, channel, slideview, types='', sorting='', search='', tags=''):
        user = request.env.user
        most_viewed_ids = slideview._get_most_viewed_slides(self._slides_per_list)
        related_ids = slideview.sudo()._get_related_slides(self._slides_per_list)

        comments = slideview.website_message_ids

        values = {
            'most_viewed_ids':most_viewed_ids,
            'related_ids': related_ids,
            'channel': slideview.channel_id,
            'user':user,
            'types':types,
            'is_public_user': user.id == request.website.user_id.id,
            'is_super_user': user.id == user.sudo().id,
            'private':True,
            'slideview_id':slideview.id,
            'type':slideview.slide_type,
            'slidename':slideview.name,
            'twitter':0,
            'facebook':0,
            'linkedin':0,
            'google':0
        }

        if slideview.channel_id.visiblity in ('private', 'semiprivate') and user != SUPERUSER_ID:
            access = False
            for group in slideview.channel_id.group_ids:
                if user in group.sudo().users:
                    access = True
                    break

            if access:
                values.update({
                    'slideview':slideview,
                    'comments': comments,
                    'private':False
                })

        if slideview.channel_id.visiblity == 'public' or user == SUPERUSER_ID:
            values.update({
                'slideview':slideview,
                'comments': comments,
                'private':False
            })

        return values


    @http.route([
                '/slides/<model("slide.channel"):channel>/<types>/<model("ir.attachment"):slideview>',
                '/slides/<model("slide.channel"):channel>/<types>/tag/<tags>/<model("ir.attachment"):slideview>'
                ], type='http', auth="public", website=True)
    def slide_view(self, channel, slideview, types='', sorting='', search='', tags=''):
        values = self.getslide(channel, slideview, types, sorting, search, tags)
        slideview.sudo().set_viewed()
        return request.website.render('website_slides.slide_view', values)


    @http.route('/slides/embed/count', type='http', auth='public', website=True)
    def slides_embed_count(self, slide, url):
        request.env['ir.attachment.embed'].sudo().set_count(slide, url)


    @http.route('/slides/editmessage/<model("slide.channel"):channel>', type='http', auth="user", website=True)
    def change_error_message(self, channel):
        values = {
            'channel':channel
        }
        return request.website.render('website_slides.privatedit', values)

    @http.route('/slides/comment/<model("ir.attachment"):slideview>', type='http', auth="public", methods=['POST'], website=True)
    def slides_comment(self, slideview, **post):
        attachment = request.env['ir.attachment']
        if post.get('comment'):
            user = request.env.user
            attachment = request.env['ir.attachment']
            attachment.check_access_rights('read')
            self._slides_message(user, slideview.id, **post)
        return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")

    @http.route('/slides/get_tags', type='http', auth="public", methods=['GET'], website=True)
    def tag_read(self, **post):
        tags = request.env['ir.attachment.tag'].search_read([], ['name'])
        data = [tag['name'] for tag in tags]
        return simplejson.dumps(data)

    @http.route('/slides/<model("slide.channel"):channel>/view/<model("ir.attachment"):slideview>/like', type='json', auth="public", website=True)
    def slide_like(self, channel, slideview, **post):
        if slideview.sudo().set_like():
            return slideview.likes
        return {'error': 'Error on wirte Data'}

    @http.route('/slides/<model("slide.channel"):channel>/view/<model("ir.attachment"):slideview>/dislike', type='json', auth="public", website=True)
    def slide_dislike(self, channel, slideview, **post):
        if slideview.sudo().set_dislike():
            return slideview.dislikes

        return {'error': 'Error on wirte Data'}

    @http.route(['/slides/sendbymail/<model("ir.attachment"):slide>'], type='json', auth='user', methods=['POST'], website=True)
    def sendbymail(self, slide, email):
        result = slide.sendemail(email)
        return result

    @http.route(['/slides/add_slide'], type='json', auth='user', methods=['POST'], website=True)
    def create_slide(self, *args, **post):
        Tag = request.env['ir.attachment.tag']

        if request.env['ir.attachment'].search([('name','=',post['name']),('channel_id','=',post['channel_id'])]):
            return {'error':'This title already exists in the channel, rename and try again.'}

        tags = post.get('tag_ids')
        tag_ids = []
        for tag in tags:
            tag_id = Tag.search([('name', '=', tag)])
            if tag_id:
                tag_ids.append((4, tag_id[0].id))
            else:
                tag_ids.append((0, 0, {'name': tag}))
            post['tag_ids'] = tag_ids
        slide_obj = request.env['ir.attachment']

        _file_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']

        if post.get('mimetype') in _file_types:
            post['slide_type'] = 'infographic'
            post['image'] = post.get('datas')

        if post.get('url') and not post.get('datas', False):
            post['slide_type'] = 'video'
        elif post.get('mimetype') == 'application/pdf':
            height = post.get('height', 0)
            width = post.get('width', 0)

            if height > width:
                post['slide_type'] = 'document'
            else:
                post['slide_type'] = 'presentation'

        slide_id = slide_obj.create(post)
        return {'url': "/slides/%s/%s/%s" % (post.get('channel_id'), post['slide_type'], slide_id.id)}

    @http.route('/slides/overlay/<model("ir.attachment"):slide>', type='json', auth="public", website=True)
    def get_next_slides(self, slide):
        slides_to_suggest = 9
        suggested_ids = slide._get_related_slides(slides_to_suggest)
        if len(suggested_ids) < slides_to_suggest:
            slides_to_suggest = slides_to_suggest - len(suggested_ids)
            suggested_ids += slide._get_most_viewed_slides(slides_to_suggest)

        vals = []
        for suggest in suggested_ids:
            val = {
                'img_src':'/website/image/ir.attachment/%s/image_thumb' % (suggest.id),
                'caption':suggest.name,
                'url':suggest._get_share_url()
            }
            vals.append(val)

        return vals

    @http.route('/slides/get_category/<model("slide.channel"):channel>', type='json', auth="public", website=True)
    def get_category(self, channel):
        category = request.env['ir.attachment.category']
        categorys = category.name_search(name='', args=[('channel_id','=',channel.id)], operator='ilike', limit=100)
        res = []
        for category in categorys:
            res.append({
                'id': category[0],
                    'name': category[1]
            })
        return res

    @http.route('/slides/embed/<model("ir.attachment"):slide>', type='http', auth='public', website=True)
    def slides_embed(self, slide, page="1"):
        values = self.getslide(channel=False, slideview=slide, types=False, sorting=False, search=False, tags=False)
        slide.sudo().set_embed_viewed()

        values.update({
            'page':page,
        })
        return request.website.render('website_slides.pdfembed', values)
