# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import werkzeug
from urlparse import urlparse
import simplejson

from openerp import SUPERUSER_ID

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website.models.website import slug

class main(http.Controller):

    _slides_per_page = 12
    _slides_per_list = 20

    def _slides_message(self, user, attachment_id=0, **post):
        cr, uid, context = request.cr, request.uid, request.context
        attachment = request.registry['ir.attachment']
        partner_obj = request.registry['res.partner']

        if uid != request.website.user_id.id:
            partner_ids = [user.partner_id.id]
        else:
            partner_ids = attachment._find_partner_from_emails(cr, SUPERUSER_ID, 0, [post.get('email')], context=context)
            if not partner_ids or not partner_ids[0]:
                partner_ids = [partner_obj.create(cr, SUPERUSER_ID, {'name': post.get('name'), 'email': post.get('email')}, context=context)]

        message_id = attachment.message_post(
            cr, SUPERUSER_ID, int(attachment_id),
            body=post.get('comment'),
            type='comment',
            subtype='mt_comment',
            author_id=partner_ids[0],
            path=post.get('path', False),
            context=dict(context, mail_create_nosubcribe=True))
        return message_id


    @http.route('/channel', type='http', auth="public", website=True)
    def channels(self, *args, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        directory = pool['document.directory']
        user = pool['res.users'].browse(cr, uid, uid, context)
        ids = directory.search(cr, uid, [('website_published','=', True)], context=context)
        
        if len(ids) <= 1:
            return request.redirect("/channel/%s" % ids[0])

        channels = directory.browse(cr, uid, ids, context)
        vals = {
            'channels': channels, 
            'user': user, 
            'is_public_user': user.id == request.website.user_id.id
        }
        return request.website.render('website_slides.channels', vals)


    @http.route(['/channel/<model("document.directory"):channel>',
                '/channel/<model("document.directory"):channel>/<types>',
                '/channel/<model("document.directory"):channel>/<types>/tag/<tags>',
                '/channel/<model("document.directory"):channel>/page/<int:page>',
                '/channel/<model("document.directory"):channel>/<types>/page/<int:page>',
                '/channel/<model("document.directory"):channel>/<types>/tag/<tags>/page/<int:page>',
                   ], type='http', auth="public", website=True)
    def slides(self, channel=0, page=1, types='', tags='', sorting='creation', search=''):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context

        user = request.registry['res.users'].browse(cr, uid, request.uid, context)
        publisher = request.registry['res.users'].has_group(cr, request.uid, 'base.group_website_publisher')
        attachment = request.registry['ir.attachment']
        domain = [('is_slide','=','True'), ('parent_id','=',channel.id)]

        count_all = count_slide = count_video = count_document = count_infographic = 0
        attachment_ids = videos = slides = documents = infographics = []
        famous = None

        if request.uid == 3: domain += [('website_published', '=', True)]
        
        all_count = attachment.search(cr, uid, domain, count=True, context=context)

        if channel: domain += [('parent_id','=',channel.id)]

        if search: domain += ['|', ('name', 'ilike', search), ('index_content', 'ilike', search)]

        if tags: domain += [('tag_ids.name', '=', tags)]

        values = {
            'tags':tags,
            'channel': channel,
            'user': user,
            'is_public_user': user.id == request.website.user_id.id,
            'publisher': publisher
        }

        if types:
            domain += [('slide_type', '=', types)]

            if sorting == 'date':
                order = 'write_date desc'
            elif sorting == 'view':
                order = 'slide_views desc'
            else:
                sorting = 'creation'
                order = 'create_date desc'

            url = "/channel/%s" % (channel.id)
            if types:
                url = "/channel/%s/%s" % (channel.id, types)
            elif types and tags:
                url = "/channel/%s/%s/%s" % (channel.id, types, tags)

            url_args = {}
            if search:
                url_args['search'] = search
            if sorting:
                url_args['sorting'] = sorting

            pager_count = attachment.search(cr, uid, domain, count=True, context=context)
            pager = request.website.pager(url=url, total=pager_count, page=page,
                                          step=self._slides_per_page, scope=self._slides_per_page,
                                          url_args=url_args)
            
            obj_ids = attachment.search(cr, uid, domain, limit=self._slides_per_page, offset=pager['offset'], order=order, context=context)
            attachment_ids = attachment.browse(cr, uid, obj_ids, context=context)
            
            values.update({
                'attachment_ids': attachment_ids,
                'all_count': len(attachment_ids),
                'pager': pager,
                'types': types,
                'sorting': sorting,
                'search': search
            })
        else:
            count_domain = domain + [('slide_type', '=', 'video')]
            count_ids = attachment.search(cr, uid, count_domain, limit=4, offset=0, order='create_date desc', context=context)
            if count_domain:
                videos = attachment.browse(cr, uid, count_ids)

            lens = {
                'video': len(count_ids)
            }
            count_domain = domain + [('slide_type', '=', 'presentation')]
            count_ids = attachment.search(cr, uid, count_domain, limit=4, offset=0, order='create_date desc', context=context)
            if count_domain:
                slides = attachment.browse(cr, uid, count_ids)
            lens.update({'presentation':len(count_ids)})

            count_domain = domain + [('slide_type', '=', 'document')]
            count_ids = attachment.search(cr, uid, count_domain, limit=4, offset=0, order='create_date desc', context=context)
            if count_domain:
                documents = attachment.browse(cr, uid, count_ids)
            lens.update({'document':len(count_ids)})

            count_domain = domain + [('slide_type', '=', 'infographic')]
            count_ids = attachment.search(cr, uid, count_domain, limit=4, offset=0, order='create_date desc', context=context)
            if count_domain:
                infographics = attachment.browse(cr, uid, count_ids)
            lens.update({'infographic':len(count_ids)})

            famous = request.registry.get('document.directory').get_mostviewed(cr, uid, channel, context)
            values.update({
                'videos':videos,
                'slides':slides,
                'documents':documents,
                'infographics': infographics,
                'famous':famous
            })

            counts = attachment.read_group(cr, uid, domain, ['slide_type'], groupby='slide_type')
            countvals = {}
            for count in counts:
                countvals['count_'+count.get('slide_type')] = count.get('slide_type_count') - lens.get(count.get('slide_type'))

            values.update(countvals)

        return request.website.render('website_slides.home', values)

    @http.route([
                '/channel/<model("document.directory"):channel>/<types>/<model("ir.attachment"):slideview>',
                '/channel/<model("document.directory"):channel>/<types>/tag/<tags>/<model("ir.attachment"):slideview>'
                ], type='http', auth="public", website=True)
    def slide_view(self, channel, slideview, types='', sorting='', search='', tags=''):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        attachment = request.registry['ir.attachment']
        user = request.registry['res.users'].browse(cr, uid, uid, context=context)

        domain = [('is_slide','=',True)]
        # increment view counter
        attachment.set_viewed(cr, uid, [slideview.id], context=context)

        # most viewed slides
        ids = attachment.search(cr, uid, domain, limit=self._slides_per_list, offset=0, order='slide_views desc', context=context)
        most_viewed_ids = attachment.browse(cr, uid, ids, context=context)

        # related slides
        tags = slideview.tag_ids.ids
        if tags:
            domain += [('tag_ids', 'in', tags)]
        ids = attachment.search(cr, uid, domain, limit=self._slides_per_list, offset=0, context=context)
        related_ids = attachment.browse(cr, uid, ids, context=context)

        # get comments
        comments = slideview.website_message_ids

        values= {
            'slideview':slideview,
            'most_viewed_ids':most_viewed_ids,
            'related_ids': related_ids,
            'comments': comments,
            'channel': slideview.parent_id,
            'user':user,
            'types':types
        }
        return request.website.render('website_slides.slide_view', values)


    @http.route('/slides/comment/<model("ir.attachment"):slideview>', type='http', auth="public", methods=['POST'], website=True)
    def slides_comment(self, slideview, **post):
        cr, uid, context = request.cr, request.uid, request.context
        attachment = request.registry['ir.attachment']
        if post.get('comment'):
            user = request.registry['res.users'].browse(cr, uid, uid, context=context)
            attachment = request.registry['ir.attachment']
            attachment.check_access_rights(cr, uid, 'read')
            self._slides_message(user, slideview.id, **post)
        return werkzeug.utils.redirect(request.httprequest.referrer + "#discuss")


    @http.route('/slides/thumb/<int:document_id>', type='http', auth="public", website=True)
    def slide_thumb(self, document_id=0, **post):
        cr, uid, context = request.cr, SUPERUSER_ID, request.context
        response = werkzeug.wrappers.Response()
        Files = request.registry['ir.attachment']
        Website = request.registry['website']
        user = Files.browse(cr, uid, document_id, context=context)
        return Website._image(cr, uid, 'ir.attachment', user.id, 'image', response)


    @http.route('/slides/get_tags', type='http', auth="public", methods=['GET'], website=True)
    def tag_read(self, **post):
        tags = request.registry['ir.attachment.tag'].search_read(request.cr, request.uid, [], ['name'], context=request.context)
        data = [tag['name'] for tag in tags]
        return simplejson.dumps(data)
    
    @http.route('/channel/<model("document.directory"):channel>/view/<model("ir.attachment"):slideview>/like', type='json', auth="public", website=True)
    def slide_like(self, channel, slideview, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        slide_obj = pool['ir.attachment']
        likes = slideview.likes + 1
        if slide_obj.write(cr, uid, [slideview.id], {'likes':likes}, context):
            return likes
        return {'error': 'Error on wirte Data'}

    @http.route('/channel/<model("document.directory"):channel>/view/<model("ir.attachment"):slideview>/dislike', type='json', auth="public", website=True)
    def slide_dislike(self, channel, slideview, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        slide_obj = pool['ir.attachment']
        dislikes = slideview.dislikes + 1
        if slide_obj.write(cr, uid, [slideview.id], {'dislikes':dislikes}, context):
            return dislikes
        return {'error': 'Error on wirte Data'}

    @http.route('/slides/get_channel', type='json', auth="public", website=True)
    def get_channel(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        directory = pool['document.directory']
        attachment = request.registry['ir.attachment']
        channels = directory.name_search(cr, uid, name='', args=[('website_published','=', True)], operator='ilike', context=context, limit=100)
        default_channel = attachment.get_default_channel(cr, uid, context)
        res = []
        for channel in channels:
            res.append({'id': channel[0],
                        'name': channel[1]
                        })
        return res

    @http.route(['/slides/add_slide'], type='http', auth="user", methods=['POST'], website=True)
    def create_slide(self, *args, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        Tag = pool['ir.attachment.tag']
        tag_ids = []
        if post.get('tag_ids').strip('[]'):
            tags = post.get('tag_ids').strip('[]').replace('"', '').split(",")
            for tag in tags:
                tag_id = Tag.search(cr, uid, [('name', '=', tag)], context=context)
                if tag_id:
                    tag_ids.append((4, tag_id[0]))
                else:
                    tag_ids.append((0, 0, {'name': tag}))
        post['tag_ids'] = tag_ids
        slide_obj = pool.get('ir.attachment')

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

            del post['height']
            del post['width']

        slide_id = slide_obj.create(cr, uid, post, context=context)
        return request.redirect("/channel/%s/%s/%s" % (post.get('parent_id'), post['slide_type'], slide_id))
