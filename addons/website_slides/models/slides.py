# -*- coding: utf-8 -*-

import io

import json
import urllib2
import requests
import cStringIO
from PIL import Image

from urlparse import urlparse,parse_qs

from openerp import models, fields, api, _
from openerp.addons.website.models.website import slug

from openerp.tools import mail

class ir_attachment_tags(models.Model):
    _name = 'ir.attachment.tag'
    name = fields.Char()


class Channel(models.Model):
    _name = 'slide.channel'
    _inherit = ['mail.thread', 'website.seo.metadata']

    name = fields.Char(string="Name", tranalate=True, required=True)

    website_published = fields.Boolean(string='Publish', help="Publish on the website", copy=False)
    description = fields.Text(string='Website Description', tranalate=True)
    website_description = fields.Html('Website Description', tranalate=True)
    slide_id = fields.Many2one('ir.attachment', string='Promoted Presentation')
    is_channel = fields.Boolean(string='Is Channel', default=False)
    promote = fields.Selection([('donot','Do not Promote'), ('latest','Newest'), ('mostvoted','Most Popular'), ('mostview','Most Viewed'), ('custom','Promote my Presentation')], string="Promoted Video", default='donot', required=True)

    presentations = fields.Integer(compute='_compute_presentations', string="Presentations")
    documents = fields.Integer(compute='_compute_presentations', string="Documents")
    videos = fields.Integer(compute='_compute_presentations', string="Videos")
    infographics = fields.Integer(compute='_compute_presentations', string="Infographics")

    total = fields.Integer(compute='_compute_presentations', string="Total")

    sequence = fields.Integer(string="Priority")
    errormessage = fields.Html('Error Message')

    template_id = fields.Many2one('email.template', 'Email Notify Template')

    visiblity = fields.Selection([('public','Public'), ('private','Hide Channel'), ('semiprivate','Show channel but presentations based on groups')], string='Visiblity', default='public')
    group_ids = fields.Many2many('res.groups', 'rel_attachments_groups', 'attachment_id', 'group_id', string='Accessible Groups')

    @api.multi
    def _compute_presentations(self):
        attachment = self.env['ir.attachment']
        for record in self:
            domain = [('is_slide','=',True), ('website_published','=',True), ('channel_id','=',record.id)]
            counts = attachment.read_group(domain, ['slide_type'], groupby='slide_type')
            countvals = {}
            for count in counts:
                countvals[count.get('slide_type')] = count.get('slide_type_count', 0)

            record.presentations = countvals.get('presentation', 0)
            record.documents = countvals.get('document', 0)
            record.videos = countvals.get('video', 0)
            record.infographics = countvals.get('infographic', 0)

            record.total = countvals.get('presentation', 0) + countvals.get('document', 0) + countvals.get('video', 0) + countvals.get('infographic', 0)

    def get_mostviewed(self):
        attachment = self.env['ir.attachment']
        famous = None
        if self.promote == 'mostview':
            domain = [('website_published', '=', True), ('channel_id','=',self.id)]
            famous = attachment.search(domain, limit=1, offset=0, order="total_views desc")
        elif self.promote == 'mostvoted':
            domain = [('website_published', '=', True), ('channel_id','=',self.id)]
            famous = attachment.search(domain, limit=1, offset=0, order="likes desc")
        elif self.promote == 'latest':
            domain = [('website_published', '=', True), ('channel_id','=',self.id)]
            famous = attachment.search(domain, limit=1, offset=0, order="write_date desc")
        elif self.promote == 'custom':
                famous = self.slide_id
        return famous


class Categoty(models.Model):
    _name = 'ir.attachment.category'
    _inherit = ['mail.thread', 'website.seo.metadata']
    _description = "Category of Documents"
    _order = "sequence"

    channel_id = fields.Many2one('slide.channel', string="Channel")
    name = fields.Char(string="Category", tranalate=True)
    sequence = fields.Integer(string='Sequence', default=10)

    presentations = fields.Integer(compute='_compute_presentations', string="Presentations")
    documents = fields.Integer(compute='_compute_presentations', string="Documents")
    videos = fields.Integer(compute='_compute_presentations', string="Videos")
    infographics = fields.Integer(compute='_compute_presentations', string="Infographics")

    total = fields.Integer(compute='_compute_presentations', string="Total")

    @api.multi
    def _compute_presentations(self):
        attachment = self.env['ir.attachment']
        for record in self:
            domain = [('is_slide','=',True), ('website_published','=',True), ('category_id','=',record.id)]
            counts = attachment.read_group(domain, ['slide_type'], groupby='slide_type')
            countvals = {}
            for count in counts:
                countvals[count.get('slide_type')] = count.get('slide_type_count')

            record.presentations = countvals.get('presentation', 0)
            record.documents = countvals.get('document', 0)
            record.videos = countvals.get('video', 0)
            record.infographics = countvals.get('infographic', 0)

            record.total = countvals.get('presentation', 0) + countvals.get('document', 0) + countvals.get('video', 0) + countvals.get('infographic', 0)

    @api.multi
    def get_slides(self, domain, limit, order):
        slides = self.env['ir.attachment']
        context_domain = domain + [('category_id', '=', self.id)]
        slides_ids = slides.search(context_domain, limit=limit, offset=0, order=order)
        return slides_ids


class EmbededView(models.Model):
    _name = 'ir.attachment.embed'

    attachment_id = fields.Many2one('ir.attachment', string="Presentation")
    name = fields.Char('Name')
    count_views = fields.Integer(string='# Views on Embed', default=0)

    def set_count(self, attachment_id, url):
        baseurl = url
        urls = url.split('?')
        if urls:
            baseurl = urls[0]
        domain = [('name','=',baseurl), ('attachment_id','=',int(attachment_id))]
        count = self.search(domain, limit=1)
        if count:
            count.count_views += 1
        else:
            vals = {
                'attachment_id':attachment_id,
                'name':baseurl,
                'count_views':1
            }
            self.create(vals)


class ir_attachment(models.Model):
    _name = 'ir.attachment'
    _inherit = ['ir.attachment','mail.thread', 'website.seo.metadata']

    category_id = fields.Many2one('ir.attachment.category', string="Category")
    embedcount_ids = fields.One2many('ir.attachment.embed', 'attachment_id', string="Embed Count")
    channel_id = fields.Many2one('slide.channel', string="Channel")
    is_slide = fields.Boolean(string='Is Slide')
    slide_type = fields.Selection([('infographic','Infographic'), ('presentation', 'Presentation'), ('document', 'Document'), ('video', 'Video')], string='Type', help="Document type will be set automatically depending on the height and width, however you can change it manually.")
    tag_ids = fields.Many2many('ir.attachment.tag', 'rel_attachments_tags', 'attachment_id', 'tag_id', string='Tags')

    image = fields.Binary('Image')
    image_meduim = fields.Binary('Medium')
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
    website_description = fields.Html('Website Description', tranalate=True)
    likes = fields.Integer(string='Likes', default=0)
    dislikes = fields.Integer(string='Dislikes', default=0)
    index_content = fields.Text('Description', tranalate=True)

    height = fields.Integer(string='Height', default=600)
    width = fields.Integer(string='Width', default=800)

    slide_views = fields.Integer(string='# Views', default=0)
    embed_views = fields.Integer(string='# Views on Embed', default=0)
    youtube_views = fields.Integer(string='# Views on Embed', default=0)

    total_views = fields.Integer(compute='_compute_total', string="Total", store=True)

    @api.multi
    @api.depends('slide_views',  'embed_views',  'youtube_views')
    def _compute_total(self):
        for record in self:
            record.total_views = record.slide_views + record.embed_views + record.youtube_views

    @api.multi
    def _get_related_slides(self, limit=20):
        domain = [('is_slide','=',True), ('website_published', '=', True), ('id','!=',self.id), ('category_id','=',self.category_id.id)]
        related_ids = self.search(domain, limit=limit, offset=0)
        return related_ids

    @api.multi
    def _get_most_viewed_slides(self, limit=20):
        domain = [('is_slide','=',True), ('website_published', '=', True)]
        most_viewed_ids = self.search(domain, limit=limit, offset=0, order='total_views desc')
        return most_viewed_ids

    @api.multi
    def check_constraint(self, values):
        if values.get('video_id'):
            domain = [('channel_id','=',values['channel_id']),('youtube_id','=',values['video_id'])]
            slide = self.search(domain)
            if slide:
                return "/slides/%s/%s/%s" % (slide.channel_id.id, slide.slide_type, slide.id)
        if values.get('file_name'):
            domain = [('channel_id','=',values['channel_id']),('name','=',values['file_name'])]
            if self.search(domain):
                return True
        return False

    def _get_share_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        shareurl = "%s/slides/%s/%s/%s" % (base_url, slug(self.channel_id), self.slide_type, slug(self))
        return shareurl

    get_share_url = _get_share_url

    def _get_thumb_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        shareurl = "%s/website/image/ir.attachment/%s/image_meduim" % (base_url, self.id)
        return shareurl

    def _get_embade_code(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        embedcode = False
        if self.datas and not self.youtube_id:
            embedcode = '<iframe  src="%s/slides/embed/%s?page=1" allowFullScreen="true" height="%s" width="%s" frameborder="0"></iframe>' % (base_url, self.id, self.height + 100, self.width)
        if self.youtube_id:
            embedcode = '<iframe src="//www.youtube.com/embed/%s?theme=light" frameborder="0"></iframe>' % (self.youtube_id)
        return embedcode

    def set_viewed(self):
        #TODO: need to decide which one is better API or SQL
        #self._cr.execute("""UPDATE ir_attachment SET slide_views = slide_views+1 WHERE id IN %s""", (self._ids,))
        self.slide_views += 1
        return True

    def set_embed_viewed(self):
        #TODO: need to decide which one is better API or SQL
        #self._cr.execute("""UPDATE ir_attachment SET embed_views = embed_views+1 WHERE id IN %s""", (self._ids,))
        self.embed_views += 1
        return True

    def set_like(self):
        self._cr.execute("""UPDATE ir_attachment SET likes = likes+1 WHERE id IN %s""", (self._ids,))
        return True

    def set_dislike(self):
        self._cr.execute("""UPDATE ir_attachment SET dislikes = dislikes+1 WHERE id IN %s""", (self._ids,))
        return True

    def get_mail_body(self, message=False):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        template = self.env['email.template']
        image_url = "%s/website/image/ir.attachment/%s/image" % (base_url, self.id)
        
        msg_context = {
            'message': message or '%s has shared %s with you !' % (self.env.user.name, self.slide_type),
            'image_url': image_url,
            'access_url':self._get_share_url(),
            'base_url':base_url
        }
        msg_context.update(self._context)
        
        message_body = template.with_context(msg_context).render_template(self.channel_id.template_id.body_html, 'ir.attachment', self.id)
        return message_body

    def sendemail(self, email):
        result = False
        body = self.get_mail_body()
        subject = '%s has shared %s with you !' % (self.env.user.name, self.slide_type)

        if self.env.user.email:
            result = mail.email_send(email_from=self.env.user.email, email_to=[email], subject=subject, body=body, reply_to=self.env.user.email, subtype="html")
        
        return result

    def notify_published(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if not self.website_published:
            return False

        message = "A new %s has been published on %s channel." % (self.slide_type, self.channel_id.name)
        body = self.get_mail_body(message=message)
        if self.channel_id:
            self.channel_id.message_post(subject=self.name, body=body, subtype='website_slides.new_slides')

    def notify_request_to_approve(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        message = "A new %s has been uploaded and waiting for publish on %s channel." % (self.slide_type, self.channel_id.name)
        body = self.get_mail_body(message=message)
        if self.channel_id:
            self.channel_id.message_post(subject=message, body=body, subtype='website_slides.new_slides_validation')

    @api.multi
    def write(self, values):
        if values.get('url'):
            values = self.update_youtube(values)
        success = super(ir_attachment, self).write(values)
        self.notify_published()
        return success

    def update_youtube(self, values):
        values["youtube_id"] = self.extract_youtube_id(values['url'].strip())
        statistics = self.youtube_statistics(values["youtube_id"])
        if statistics:
            if statistics['items'][0].get('snippet'):
                if statistics['items'][0]['snippet'].get('thumbnails'):
                    image_url = statistics['items'][0]['snippet']['thumbnails']['medium']['url']
                    response = requests.get(image_url)
                    if response:
                        values['image'] = response.content.encode('base64')
                if statistics['items'][0]['snippet'].get('description'):
                        values['description'] = statistics['items'][0]['snippet'].get('description')
            if statistics['items'][0].get('statistics'):
                values['youtube_views'] = int(statistics['items'][0]['statistics']['viewCount'])
        return values

    #TODO: to check, may be useful to place this image in to website module
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
            cropped_image.save(output,format=image_format)
        elif type == "center":
            cropped_image = image.crop(((w - new_w)/2, (h - new_h)/2, (w + new_w)/2, (h + new_h)/2))
            cropped_image.save(output,format=image_format)
        elif type == "bottom":
            cropped_image = image.crop((0, h - new_h, new_w, h))
            cropped_image.save(output,format=image_format)
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        if thumbnail_ratio:
            thumb_image = Image.open(cStringIO.StringIO(output.getvalue()))
            thumb_image.thumbnail((new_w/thumbnail_ratio, new_h/thumbnail_ratio), Image.ANTIALIAS)
            output = io.BytesIO()
            thumb_image.save(output, image_format)
        return output.getvalue().encode('base64')

    @api.model
    def create(self, values):
        if values.get('is_slide'):
            if values.get('datas_fname'):
                values['url'] = "/website_slides/" + values['datas_fname']
            elif values.get('url'):
                values = self.update_youtube(values)

        if not values.get('index_content'):
            values['index_content'] = values.get('description')

        if values.get('image') and values.get('slide_type') == 'video':
            values.update({
                'image_meduim': values.get('image'),
                'image_thumb': values.get('image')
            })
        elif values.get('image'):
            image_meduim = self.crop_image(values['image'], thumbnail_ratio=3)
            image_thumb = self.crop_image(values['image'], thumbnail_ratio=4)
            image = self.crop_image(values['image'])
            values.update({
                'image_meduim': image_meduim,
                'image_thumb': image_thumb,
                'image': image
            })

        values['total_views'] = values.get('slide_views', 0) + values.get('youtube_views', 0)
        slide_id = super(ir_attachment, self).create(values)
        slide_id.notify_request_to_approve()
        slide_id.notify_published()
        return slide_id

    def extract_youtube_id(self, url):
        youtube_id = ""
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            youtube_id = query.path[1:]
        elif query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                p = parse_qs(query.query)
                youtube_id = p['v'][0]
            elif query.path[:7] == '/embed/':
                youtube_id = query.path.split('/')[2]
            elif query.path[:3] == '/v/':
                youtube_id = query.path.split('/')[2]
        return youtube_id

    def youtube_statistics(self, video_id):
        request_url = "https://www.googleapis.com/youtube/v3/videos?id=%s&key=AIzaSyBKDzf7KjjZqwPWAME6JOeHzzBlq9nrpjk&part=snippet,statistics&fields=items(id,snippet,statistics)" % (video_id)
        try:
            req = urllib2.Request(request_url)
            content = urllib2.urlopen(req).read()
        except urllib2.HTTPError:
            return False
        return json.loads(content)
