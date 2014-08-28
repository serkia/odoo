# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import logging

import openerp

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class loyalty_program(osv.osv):
    _name = 'loyalty.program'
    _columns = {
        'name' :        fields.char('Loyalty Program Name', size=32, select=1,
             required=True, help="An internal identification for the loyalty program configuration"),
        'pp_currency':  fields.float('Points per currency',help="How many loyalty points are given to the customer by sold currency"),
        'pp_product':   fields.float('Points per product',help="How many loyalty points are given to the customer by product sold"),
        'pp_order':     fields.float('Points per order',help="How many loyalty points are given to the customer for each sale or order"),
        'rounding':     fields.float('Points Rounding', help="The loyalty point amounts are rounded to multiples of this value."),
        'rule_ids':     fields.one2many('loyalty.rule','loyalty_program_id','Rules'),
        'reward_ids':   fields.one2many('loyalty.reward','loyalty_program_id','Rewards'),
        
    }
    _defaults = {
        'rounding': 1,
    }

class loyalty_rule(osv.osv):
    _name = 'loyalty.rule'
    _columns = {
        'name':                 fields.char('Name', size=32, select=1, required=True, help="An internal identification for this loyalty program rule"),
        'loyalty_program_id':   fields.many2one('loyalty.program', 'Loyalty Program', help='The Loyalty Program this exception belongs to'),
        'product_id':           fields.many2one('product.product','Target Product', help='The product affected by the rule'),
        'override':             fields.boolean('Override Base Rules',      help='A product targetted by this rule will be ignored by other loyalty rules, including the default one'),
        'pp_product':           fields.float('Points per product',  help='How many points the product will earn per product ordered'),
        'pp_currency':          fields.float('Points per currency', help='How many points the product will earn per value sold'),
    }

class loyalty_reward(osv.osv):
    _name = 'loyalty.reward'
    _columns = {
        'name':                 fields.char('Name', size=32, select=1, required=True, help='An internal identification for this loyalty reward'),
        'loyalty_program_id':   fields.many2one('loyalty.program', 'Loyalty Program', help='The Loyalty Program this reward belongs to'),
        'minimum_points':       fields.float('Minimum Points', help='The minimum amount of points the customer must have to be eligible for this reward'),
        'type':                 fields.selection((('gift','Gift'),('discount','Discount')), 'Type', required=True, help='The type of the reward'),
        'gift_product_id':           fields.many2one('product.product','Gift Product', help='The product given as a reward'),
        'point_cost':           fields.float('Point Cost', help='The cost of the reward'),
        'discount_product_id':  fields.many2one('product.product','Discount Product', help='The product used to apply discounts'),
        'discount':             fields.float('Discount',help='The discount percentage'),
    }

class pos_config(osv.osv):
    _inherit = 'pos.config' 
    _columns = {
        'loyalty_id': fields.many2one('loyalty.program','Loyalty Program', help='The loyalty program used by this point_of_sale'),
        
    }

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'loyalty_points': fields.float('Loyalty Points', help='The loyalty points the user won as part of a Loyalty Program')
    }

class pos_order(osv.osv):
    _inherit = 'pos.order'

    _columns = {
        'loyalty_points': fields.float('Loyalty Points', help='The amount of Loyalty points the customer won or lost with this order'),
    }

    def _order_fields(self, cr, uid, ui_order, context=None):
        fields = super(pos_order,self)._order_fields(cr,uid,ui_order,context)
        fields['loyalty_points'] = ui_order['loyalty_points']
        return fields

    def create_from_ui(self, cr, uid, orders, context=None):
        ids = super(pos_order,self).create_from_ui(cr,uid,orders,context=context)
        for order in orders:
            if 'loylaty_points' in order['data'] and order['data']['partner_id']:
                partner = self.pool.get('res.partner').browse(cr,uid,order['data']['partner_id'], context=context)
                partner.write({'loyalty_points': partner['loyalty_points'] + order['data']['loyalty_points']})

        return ids
            
             
    



