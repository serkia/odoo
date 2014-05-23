# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp.osv import fields, osv

class ProductRate(osv.Model):
    _inherit = 'product.template'
    
    def _calulate_average(self, cr, uid, ids, context=None):
        res = {'great':0,'okay':0,'bad':0}
        for product in self.browse(cr, uid, ids, context=context):
            rating_ids = self.pool.get('rating.rating').search(cr, uid, [('res_model','=','product.template'),('res_id','=',product.id)])
            for rate in self.pool['rating.rating'].browse(cr, uid, rating_ids, context):
                res[rate.state] += 1
            if len(rating_ids):
                res['great'] = ((100*res['great'])/len(rating_ids))
                res['okay'] = ((100*res['okay'])/len(rating_ids))
                res['bad'] = ((100*res['bad'])/len(rating_ids))
        return res

    def _product_average_rate(self, cr, uid, ids, names, arg, context=None):
        res = self._calulate_average(cr, uid ,ids, context)
        rating = 0.0
        img = ''
        for key,value in res.items():
            rating += value
        rating = float('%.2f' %(rating/3))
        if rating >= 90:
            img = '<img src="/rating/static/src/img/great.png"/><h3>'+str(rating)+'%</h3>'
        elif rating >= 50 and rating < 90:
            img = '<img src="/rating/static/src/img/okay.png"/><h3>'+str(rating)+'%</h3>'
        elif rating > 0 and rating < 50:
            img = '<img src="/rating/static/src/img/bad.png"/><h3>'+str(rating)+'%</h3>'
        for id in ids:
            res[id] = img
        return res

    _columns = {
        'product_average_rating': fields.function(_product_average_rate, string='Average Rating', type="html"),
        'allow_rating': fields.boolean('Allow Rating for this Product'),
    }

    _defaults = {
        'allow_rating': True,
    }
    
    def average_rate(self, cr, uid, ids, context=None):
        res = []
        result = self._calulate_average(cr, uid, ids, context)
        res.append(('great', result['great'], 'label-success'))
        res.append(('okay', result['okay'], 'label-warning'))
        res.append(('bad', result['bad'], 'label-danger'))
        res.sort(key=lambda x: x[1], reverse=True)
        return res

class Product(osv.Model):
    _inherit = 'product.product'

    def action_rating(self, cr, uid, ids, context=None):
        context = dict(context or {})
        mod_obj = self.pool['ir.model.data']
        model, action_id = mod_obj.get_object_reference(cr, uid, 'rating', 'action_view_rating')
        action = self.pool['ir.actions.act_window'].read(cr, uid, action_id, context=context)
        return dict(action , domain = [('res_id', 'in', ids), ('res_model', '=', 'product.template')])
