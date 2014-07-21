# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Users(models.Model):
    _inherit = 'res.users'

    def __init__(self, pool, cr):
        init_res = super(Users, self).__init__(pool, cr) 
        self.SELF_WRITEABLE_FIELDS = list(set(
                self.SELF_WRITEABLE_FIELDS + \
                ['country_id', 'city', 'website', 'website_description', 'website_published']))
        return init_res

    @api.multi
    @api.depends('badge_ids')
    def _get_user_badge_level(self):
        """Return total badge per level of users"""
        def map_badge(badge):
            return (badge['user_id'][0],badge['__count'])
        gold_badge = self.env['gamification.badge.user'].read_group([('badge_id.level', '=', 'gold')], ["user_id", "badge_id"], ["user_id"], lazy=False)
        silver_badge = self.env['gamification.badge.user'].read_group([('badge_id.level', '=', 'silver')], ["user_id", "badge_id"], ["user_id"], lazy=False)
        bronze_badge = self.env['gamification.badge.user'].read_group([('badge_id.level', '=', 'bronze')], ["user_id", "badge_id"], ["user_id"], lazy=False)
        gold = dict(map(map_badge, gold_badge))
        silver = dict(map(map_badge, silver_badge))
        bronze = dict(map(map_badge, bronze_badge))
        for rec in self:
            rec.gold_badge = gold.get(rec.id,0)
            rec.silver_badge = silver.get(rec.id,0)
            rec.bronze_badge = bronze.get(rec.id,0)

    create_date = fields.Datetime(string='Create Date', readonly=True, copy=False, select=True)
    karma = fields.Integer(string='Karma', default=0)
    badge_ids = fields.One2many('gamification.badge.user', 'user_id', string='Badges', copy=False)
    gold_badge = fields.Integer(string='Number of gold badges', compute="_get_user_badge_level")
    silver_badge = fields.Integer(string='Number of silver badges', compute="_get_user_badge_level")
    bronze_badge = fields.Integer(string='Number of bronze badges', compute="_get_user_badge_level")

    def add_karma(self, karma):
        self.karma += karma
        return True

    @api.model
    def get_serialised_gamification_summary(self, excluded_categories=None):
        if isinstance(excluded_categories, list):
            if 'forum' not in excluded_categories:
                excluded_categories.append('forum')
        else:
            excluded_categories = ['forum']
        return super(Users, self).get_serialised_gamification_summary()
