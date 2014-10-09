# -*- coding: utf-8 -*-

import re
import io
import json
import urllib2
import datetime
import requests
import cStringIO

from PIL import Image
from urlparse import urlparse
from openerp.tools import mail
from openerp import models, fields, api
from openerp.addons.website.models.website import slug


class Channel(models.Model):
    _name = 'slide.channel'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _description = '''Define public or private access for presentations in channels'''

    name = fields.Char(string="Name", translate=True, required=True)

    website_published = fields.Boolean(string='Publish', help="Publish on the website", copy=False)
    description = fields.Text(string='Description', translate=True)

    promote = fields.Selection([('none', 'Do not Promote'), ('latest', 'Newest'), ('popular', 'Most Popular'), ('mostview', 'Most Viewed'), ('custom', 'Promote my slide')], string="Promote Slide", default='none', required=True)

    presentations = fields.Integer(compute='_compute_presentations', string="Number of Presentations")
    documents = fields.Integer(compute='_compute_presentations', string="Number of Documents")
    videos = fields.Integer(compute='_compute_presentations', string="Number of Videos")
    infographics = fields.Integer(compute='_compute_presentations', string="Number of Infographics")
    total = fields.Integer(compute='_compute_presentations', string="Total")

    sequence = fields.Integer(string="Sequence")

    errormessage = fields.Html('Error Message', help="Html message when channel's content is not accessible for a user")
    template_id = fields.Many2one('email.template', 'Email Template', html="Email template use to send slide notification through email")

    visibility = fields.Selection([('public', 'Public'), ('private', 'Hide Channel'), ('group', 'Show channel but presentations based on groups')], string='Visiblity', default='public')
    group_ids = fields.Many2many('res.groups', 'rel_channel_groups', 'channel_id', 'group_id', string='Accessible Groups')

    @api.one
    def _compute_presentations(self):
        slide_obj = self.env['slide.slide']
        domain = [('website_published', '=', True), ('channel_id', '=', self.id)]
        counts = slide_obj.read_group(domain, ['slide_type'], groupby=['slide_type'])

        countvals = {}
        if counts:
            for count in counts:
                countvals[count.get('slide_type')] = count.get('slide_type_count', 0)

        self.presentations = countvals.get('presentation', 0)
        self.documents = countvals.get('document', 0)
        self.videos = countvals.get('video', 0)
        self.infographics = countvals.get('infographic', 0)

        self.total = self.presentations + self.documents + self.videos + self.infographics

    def get_promoted_slide(self):
        '''Return promoted slide based on the promote type'''

        slide_obj = self.env['slide.slide']
        famous = None
        if self.promote == 'mostview':
            domain = [('website_published', '=', True), ('channel_id', '=', self.id)]
            famous = slide_obj.search(domain, limit=1, offset=0, order="total_views desc")
        elif self.promote == 'popular':
            domain = [('website_published', '=', True), ('channel_id', '=', self.id)]
            famous = slide_obj.search(domain, limit=1, offset=0, order="likes desc")
        elif self.promote == 'latest':
            domain = [('website_published', '=', True), ('channel_id', '=', self.id)]
            famous = slide_obj.search(domain, limit=1, offset=0, order="date_publish desc")
        elif self.promote == 'custom':
                famous = self.slide_id
        return famous

    def set_promoted(self, slide_id):
        self.slide_id = slide_id
        return True


class Category(models.Model):
    _name = 'slide.category'
    _description = "Category of slides"
    _order = "sequence"

    channel_id = fields.Many2one('slide.channel', string="Channel")
    name = fields.Char(string="Category", tranalate=True, required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    presentations = fields.Integer(compute='_compute_presentations', string="Number of Presentations")
    documents = fields.Integer(compute='_compute_presentations', string="Number of Documents")
    videos = fields.Integer(compute='_compute_presentations', string="Number of Videos")
    infographics = fields.Integer(compute='_compute_presentations', string="Number of Infographics")
    total = fields.Integer(compute='_compute_presentations', string="Total")

    @api.one
    def _compute_presentations(self):
        slide_obj = self.env['slide.slide']
        domain = [('website_published', '=', True), ('category_id', '=', self.id)]
        counts = slide_obj.read_group(domain, ['slide_type'], groupby='slide_type')
        countvals = {}
        for count in counts:
            countvals[count.get('slide_type')] = count.get('slide_type_count')

        self.presentations = countvals.get('presentation', 0)
        self.documents = countvals.get('document', 0)
        self.videos = countvals.get('video', 0)
        self.infographics = countvals.get('infographic', 0)

        self.total = countvals.get('presentation', 0) + countvals.get('document', 0) + countvals.get('video', 0) + countvals.get('infographic', 0)

    @api.multi
    def get_slides_by_category(self, domain, limit, order):
        slides = self.env['slide.slide']
        context_domain = domain + [('category_id', '=', self.id)]
        slides_ids = slides.search(context_domain, limit=limit, offset=0, order=order)
        return slides_ids


class EmbededView(models.Model):
    _name = 'slide.embed'

    '''Track number of views on embed urls'''

    slide_id = fields.Many2one('slide.slide', string="Presentation")
    name = fields.Char('Name')
    count_views = fields.Integer(string='# Views on Embed', default=0)

    def set_count(self, slide_id, url):
        schema = urlparse(url)

        baseurl = schema.netloc
        domain = [('name', '=', baseurl), ('slide_id', '=', int(slide_id))]
        count = self.search(domain, limit=1)
        if count:
            count.count_views += 1
        else:
            vals = {
                'slide_id': slide_id,
                'name': baseurl,
                'count_views': 1
            }
            self.create(vals)


class SlideTag(models.Model):
    _name = 'slide.tag'

    name = fields.Char()


class Slide(models.Model):
    _name = 'slide.slide'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _description = '''Slides'''

    name = fields.Char('Title', required=True)
    description = fields.Text('Description', tranalate=True)
    index_content = fields.Text('Description')

    datas = fields.Binary('Content')
    url = fields.Char('Access Url')

    date_publish = fields.Datetime('Publish Date')

    channel_id = fields.Many2one('slide.channel', string="Channel", required=True)
    category_id = fields.Many2one('slide.category', string="Category")
    tag_ids = fields.Many2many('slide.tag', 'rel_slide_tag', 'slide_id', 'tag_id', string='Tags')
    embedcount_ids = fields.One2many('slide.embed', 'slide_id', string="Embed Count")

    slide_type = fields.Selection([('infographic', 'Infographic'), ('presentation', 'Presentation'), ('document', 'Document'), ('video', 'Video')], string='Type', help="Document type will be set automatically depending on the height and width, however you can change it manually.")

    image = fields.Binary('Image')
    image_medium = fields.Binary('Medium')
    image_thumb = fields.Binary('Thumbnail')

    youtube_id = fields.Char(string="Youtube Video ID")
    website_published = fields.Boolean(
        string='Publish', help="Publish on the website", copy=False, default=False
    )
    website_message_ids = fields.One2many(
        'mail.message', 'res_id',
        domain=lambda self: [('model', '=', self._name), ('type', '=', 'comment')],
        string='Website Messages', default=False,
        help="Website communication history",
    )

    likes = fields.Integer(string='Likes', default=0)
    dislikes = fields.Integer(string='Dislikes', default=0)

    height = fields.Integer(string='Height', default=600)
    width = fields.Integer(string='Width', default=800)

    slide_views = fields.Integer(string='Number of Views', default=0)
    embed_views = fields.Integer(string='Number of Views on Embed', default=0)
    youtube_views = fields.Integer(string='Number of Views on Embed', default=0)
    total_views = fields.Integer(compute='_compute_total', string="Total", store=True)

    @api.multi
    @api.depends('slide_views', 'embed_views', 'youtube_views')
    def _compute_total(self):
        for record in self:
            record.total_views = record.slide_views + record.embed_views + record.youtube_views

    @api.multi
    def get_related_slides(self, limit=20):
        domain = [('website_published', '=', True), ('id', '!=', self.id), ('category_id', '=', self.category_id.id)]
        related_ids = self.search(domain, limit=limit, offset=0)
        return related_ids

    @api.multi
    def get_most_viewed_slides(self, limit=20):
        domain = [('website_published', '=', True)]
        most_viewed_ids = self.search(domain, limit=limit, offset=0, order='total_views desc')
        return most_viewed_ids

    @api.multi
    def check_constraint(self, values):
        '''called from website to check if already available or not'''
        if values.get('video_id'):
            domain = [('channel_id', '=', values['channel_id']), ('youtube_id', '=', values['video_id'])]
            slide = self.search(domain)
            if slide:
                return "/slides/%s/%s/%s" % (slide.channel_id.id, slide.slide_type, slide.id)
        if values.get('file_name'):
            domain = [('channel_id', '=', values['channel_id']), ('name', '=', values['file_name'])]
            if self.search(domain):
                return True
        return False

    def get_share_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        shareurl = "%s/slides/%s/%s/%s" % (base_url, slug(self.channel_id), self.slide_type, slug(self))
        return shareurl

    def get_thumb_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        shareurl = "%s/website/image/slide.slide/%s/image_medium" % (base_url, self.id)
        return shareurl

    def get_embade_code(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        embedcode = False
        if self.datas and not self.youtube_id:
            embedcode = '<iframe  src="%s/slides/embed/%s?page=1" allowFullScreen="true" height="%s" width="%s" frameborder="0"></iframe>' % (base_url, self.id, self.height + 100, self.width)
        if self.youtube_id:
            embedcode = '<iframe src="//www.youtube.com/embed/%s?theme=light" frameborder="0"></iframe>' % (self.youtube_id)
        return embedcode

    def set_viewed(self):
        # TODO: need to decide which one is better API or SQL
        # self._cr.execute("""UPDATE ir_attachment SET slide_views = slide_views+1, total_views = total_views+1 WHERE id IN %s""", (self._ids,))
        self.slide_views += 1
        return True

    def set_embed_viewed(self):
        # TODO: need to decide which one is better API or SQL
        # self._cr.execute("""UPDATE ir_attachment SET embed_views = embed_views+1, total_views = total_views+1 WHERE id IN %s""", (self._ids,))
        self.embed_views += 1
        return True

    def set_like(self):
        self.likes += 1
        return True

    def set_dislike(self):
        self.dislikes += 1
        return True

    def get_mail_body(self, message=False):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        template = self.env['email.template']
        image_url = "%s/website/image/slide.slide/%s/image" % (base_url, self.id)

        msg_context = {
            'message': message or '%s has shared %s with you !' % (self.env.user.name, self.slide_type),
            'image_url': image_url,
            'access_url': self.get_share_url(),
            'base_url': base_url
        }
        msg_context.update(self._context)

        message_body = template.with_context(msg_context).render_template(self.channel_id.template_id.body_html, 'slide.slide', self.id)
        return message_body

    def sendemail(self, email):
        result = False
        body = self.get_mail_body()
        subject = '%s has shared %s with you !' % (self.env.user.name, self.slide_type)

        if self.env.user.email:
            result = mail.email_send(email_from=self.env.user.email, email_to=[email], subject=subject, body=body, reply_to=self.env.user.email, subtype="html")

        return result

    def notify_published(self):
        if not self.website_published:
            return False

        message = "A new %s has been published on %s channel." % (self.slide_type, self.channel_id.name)
        body = self.get_mail_body(message=message)
        if self.channel_id:
            self.channel_id.message_post(subject=self.name, body=body, subtype='website_slides.new_slides')

    def notify_request_to_approve(self):
        message = "A new %s has been uploaded and waiting for publish on %s channel." % (self.slide_type, self.channel_id.name)
        body = self.get_mail_body(message=message)
        if self.channel_id:
            self.channel_id.message_post(subject=message, body=body, subtype='website_slides.new_slides_validation')

    # TODO: check, may be useful to place this image in to website module
    def crop_image(self, data, type='top', ratio=False, thumbnail_ratio=None, image_format="PNG"):
        """ Used for cropping image and create thumbnail
            :param data: base64 data of image.
            :param type: Used for cropping position possible
                Possible Values : 'top', 'center', 'bottom'
            :param ratio: Cropping ratio
                e.g for (4,3), (16,9), (16,10) etc
                send ratio(1,1) to generate square image
            :param thumbnail_ratio: It is size reduce ratio for thumbnail
                e.g. thumbnail_ratio=2 will reduce your 500x500 image converted in to 250x250
            :param image_format: return image format PNG,JPEG etc
        """

        image = Image.open(cStringIO.StringIO(data.decode('base64')))
        output = io.BytesIO()
        w, h = image.size
        new_h = h
        new_w = w

        if ratio:
            w_ratio, h_ratio = ratio
            new_h = (w * h_ratio) / w_ratio
            new_w = w
            if new_h > h:
                new_h = h
                new_w = (h * w_ratio) / h_ratio

        if type == "top":
            cropped_image = image.crop((0, 0, new_w, new_h))
            cropped_image.save(output, format=image_format)
        elif type == "center":
            cropped_image = image.crop(((w - new_w)/2, (h - new_h)/2, (w + new_w)/2, (h + new_h)/2))
            cropped_image.save(output, format=image_format)
        elif type == "bottom":
            cropped_image = image.crop((0, h - new_h, new_w, h))
            cropped_image.save(output, format=image_format)
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        if thumbnail_ratio:
            thumb_image = Image.open(cStringIO.StringIO(output.getvalue()))
            thumb_image.thumbnail((new_w/thumbnail_ratio, new_h/thumbnail_ratio), Image.ANTIALIAS)
            output = io.BytesIO()
            thumb_image.save(output, image_format)
        return output.getvalue().encode('base64')

    def _detect_type(self, values):
        slide_type = 'presentation'

        _file_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif']

        if values.get('url') and not values.get('datas', False):
            slide_type = 'video'
        elif values.get('datas') and values.get('mimetype') in _file_types:
            slide_type = 'infographic'
        elif values.get('datas') and values.get('mimetype') == 'application/pdf':
            height = values.get('height', 0)
            width = values.get('width', 0)

            if height > width:
                slide_type = 'document'
            else:
                slide_type = 'presentation'

        return slide_type

    @api.multi
    def write(self, values):
        if values.get('url'):
            values = self.update_youtube(values)

        if values.get('website_published'):
            values.update({'date_publish': datetime.datetime.now()})

        success = super(Slide, self).write(values)

        if values.get('website_published'):
            self.notify_published()

        return success

    @api.model
    def create(self, values):
        if not values.get('slide_type', False):
            values['slide_type'] = self._detect_type(values)

        if values.get('url'):
            values["youtube_id"] = self.extract_youtube_id(values['url'].strip())
            vals = self.get_youtube_statistics(values['youtube_id'], part='snippet,statistics', fields='id,snippet,statistics')
            values.update(vals)

        if values.get('wesite_upload'):
            del values['wesite_upload']

        if values.get('mimetype'):
            del values['mimetype']

        if not values.get('index_content'):
            values['index_content'] = values.get('description')

        if values.get('slide_type') != 'video':
            image_medium = self.crop_image(values['image'], thumbnail_ratio=3)
            image_thumb = self.crop_image(values['image'], thumbnail_ratio=4)
            image = self.crop_image(values['image'])
            values.update({
                'image_medium': image_medium,
                'image_thumb': image_thumb,
                'image': image
            })

        if values.get('website_published'):
            values.update({'date_publish': datetime.datetime.now()})

        values['total_views'] = int(values.get('slide_views', 0)) + int(values.get('youtube_views', 0))
        slide_id = super(Slide, self).create(values)

        # notify channel manager to approve uploaded slide
        slide_id.notify_request_to_approve()

        # notify all users who subscribed to channel
        slide_id.notify_published()
        return slide_id

    def extract_youtube_id(self, url):
        youtube_id = ""
        regex_y = r'.*(?:v=|/v/|^|/youtu.be/|/embed/)(?P<id>[^&]*)'
        regex_y = re.compile(regex_y)
        erg = regex_y.match(url)
        youtube_id = erg.group('id')
        return youtube_id

    def get_youtube_statistics(self, video_id, part='statistics', fields='statistics'):
        apiurl = 'https://www.googleapis.com/youtube/v3/videos'
        key = 'AIzaSyBKDzf7KjjZqwPWAME6JOeHzzBlq9nrpjk'
        vals = None
        request_url = "%s?id=%s&key=%s&part=%s&fields=items(%s)" % (apiurl, video_id, key, part, fields)
        try:
            req = urllib2.Request(request_url)
            content = urllib2.urlopen(req).read()
            values = json.loads(content)
            vals = self.parse_youtube_statistics(values)
        except urllib2.HTTPError:
            pass
        return vals

    def parse_youtube_statistics(self, values):

        def _get_image_data(image_url):
            image_date = False
            response = requests.get(image_url)
            if response:
                image_date = response.content.encode('base64')
            return image_date

        vals = {}
        if values:
            item = values['items'][0]

            if item.get('snippet'):
                vals['image_thumb'] = _get_image_data(item['snippet']['thumbnails']['medium']['url'])
                vals['image_medium'] = _get_image_data(item['snippet']['thumbnails']['high']['url'])
                vals['image'] = _get_image_data(item['snippet']['thumbnails']['standard']['url'])

                if item['snippet'].get('description'):
                    vals['description'] = values['items'][0]['snippet'].get('description')

            if item.get('statistics'):
                vals['youtube_views'] = int(item['statistics']['viewCount'])
                vals['likes'] = int(item['statistics']['likeCount'])
                vals['dislikes'] = int(item['statistics']['dislikeCount'])

        return vals

class Channel(models.Model):
    _inherit = 'slide.channel'

    slide_id = fields.Many2one('slide.slide', string='Promote Slide')
