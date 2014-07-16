# -*- coding: utf-8 -*-

import uuid
import logging

from openerp import models, fields, api, _

_logger = logging.getLogger(__name__)


class Rating(models.Model):
    _name = "rating.rating"
    _order = 'create_date desc'

    @api.multi
    def _compute_res_name(self):
        for record in self:
            record.res_name = self.env[record.res_model].browse(record.res_id).name

    res_name = fields.Char(compute='_compute_res_name', string='Resource Name')
    res_model = fields.Char(string='Resource Model', required=True)
    res_id = fields.Integer(string='Resource ID', required=True)
    user_id = fields.Many2one('res.users', string='Rated User')
    customer_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([('great', 'Great'), ('okay', 'Okay'), ('bad', 'Not Good')], string='Select Rate')
    access_token = fields.Char(string='Security Token')

    def new_access_token(self):
        return uuid.uuid4().hex

    @api.model
    def do_great(self, res_model=None, res_id=None, token=None):
        return self.apply_rating('great', res_model, res_id, token)

    @api.model
    def do_okay(self, res_model=None, res_id=None, token=None):
        return self.apply_rating('okay', res_model, res_id , token)

    @api.model
    def do_bad(self, res_model=None, res_id=None, token=None):
        return self.apply_rating('bad', res_model, res_id, token)

    @api.model
    def apply_rating(self, state, res_model=None, res_id=None, token=None):
        rating_obj = self.env['rating.rating']
        domain = [('access_token', '=', token)] if token else [('res_model', '=', res_model), ('res_id', '=', res_id)]
        rating = rating_obj.sudo().search(domain)
        if rating:
            rating.state = state
            record = self.env[rating.res_model].sudo().browse(rating.res_id)
            record.message_post(
            body="%s %s <br/><img src='rating/static/src/img/%s.png' style='width:20px;height:20px'/>"
            % (record.partner_id.name, _('rated it'), state))
            return record
        return False

class RatingMixin(models.AbstractModel):
    _name = 'rating.mixin'

    rating_ids = fields.One2many('rating.rating', 'res_id',
            domain=lambda self: [('res_model', '=', self._name)],
            string='Rating')

    @api.multi
    def send_request(self, template):
        """
            Sends an email to the customer requesting rating
            for the Model's object from which it is called.
        """
        rating_obj = self.env['rating.rating']
        access_token = rating_obj.new_access_token()
        email_to = getattr(self, 'email_from', self.partner_id.email)
        if email_to and self.user_id.email:
            template.with_context(
                access_token=access_token,
                model=self,
                model_name=self._name,
                email_to=email_to
            ).send_mail(self.id, force_send=True)
            self.env['rating.rating'].create({'access_token': access_token, 'res_model': self._name, 'res_id': self.id,
                    'user_id': self.user_id.id, 'customer_id': self.partner_id.id})
        return False
