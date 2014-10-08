import random
import hashlib

from openerp import tools
from datetime import datetime, date
from openerp.addons.web.http import request
from openerp import models, fields, api, _

class sales_coupon_tupe(models.Model):
    _name = 'sales.coupon.type'

    name = fields.Char(string='Name', required=True, help="Coupon Name")
    validity_use = fields.Selection(
        [('expiration_date', 'Expiration Date'),
         ('expiration_use', 'Expiration Use'),
        ],'Validity Use', default='expiration_date',
        required=True)
    expiration_date = fields.Date(string='Expiration Date',
                    default=lambda self: fields.datetime.now(),
                    required=True, help="give a period")
    expiration_use = fields.Float(string='Expiration Use', required=True, help="give a limit in term of use")

class sales_coupon(models.Model):
    _name = 'sales.coupon'

    @api.multi
    def onchange_coupon_id(self, coupon_type):
        coupon_type = self.env['sales.coupon.type'].browse(coupon_type)
        return {'value': {
            'expiration_date': coupon_type.expiration_date,
            'expiration_use': coupon_type.expiration_use
            }
        }

    code = fields.Char('Coupon Code',
        default=lambda self: 'SC' + (hashlib.sha1( str(random.getrandbits(256)).encode('utf-8')).hexdigest()[:7]).upper(),
        required=True, readonly=True, help="Coupon Code")
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    coupon_type = fields.Many2one('sales.coupon.type', 'Coupon Type')
    validity = fields.Selection(
        [('expiration_date', 'Expiration Date'),
         ('expiration_use', 'Expiration Use'),
        ],'Validity', default='expiration_date',
        required=True)
    expiration_date = fields.Date(string='Expiration Date', help="give a period")
    expiration_use = fields.Float(string='Expiration Use', help="give a limit in term of use")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    state = fields.Selection([
        ('current', 'Current'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ], 'Status', default='current', readonly=True, select=True)
    order_line_id = fields.Many2one('sale.order.line', 'Order Reference', readonly=True)

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def apply_coupon(self, promocode, order):
        coupon_code_obj = self.env['sales.coupon']
        sale_order_line_obj = self.env['sale.order.line']
        order_line = sale_order_line_obj.search([('order_id', '=', order.id)])
        for order_line_obj in order_line:
            product_in_cart = coupon_code_obj.search([('code', '=', promocode),('product_id', '=', order_line_obj.product_id.id)])
            coupon = coupon_code_obj.browse(product_in_cart.id)
            if not coupon:
                product_not_in_cart= True
            if coupon and coupon.state == 'current':
                product_not_in_cart= False
                if coupon.validity == 'expiration_date':
                    date_expire = (datetime.strptime(coupon.expiration_date, tools.DEFAULT_SERVER_DATE_FORMAT).date())
                    if date_expire < datetime.now().date():
                        coupon.write({'state': 'expired' })
                        return {'error': 'coupon_expired'}
                    if order_line_obj.coupon_code:
                        product_not_in_cart = True
                    else:
                        product_not_in_cart = False
                        order_line_obj.write({'coupon_code': coupon.id })
                        sale_order_line_obj.create({
                            'order_id': order.id,
                            'name': 'Coupon : ' + promocode,
                            'price_unit': - order_line_obj.price_unit,
                            'coupon_code': coupon.id
                        })
                        return {'update_price': 'update_cart_price'}
                else:
                    if coupon.expiration_use <= 0:
                        coupon.write({'state': 'used' })
                        return {'error': 'coupon_used'}
                    if order_line_obj.coupon_code:
                        product_not_in_cart = True
                    else:
                        product_not_in_cart = False
                        order_line_obj.write({'coupon_code': coupon.id })
                        sale_order_line_obj.create({
                            'order_id': order.id,
                            'name': 'Coupon : ' + promocode,
                            'price_unit': - order_line_obj.price_unit,
                            'coupon_code': coupon.id
                        })
                        coupon.write({'expiration_use': coupon.expiration_use -1})
                        return {'update_price': 'update_cart_price'}
        if product_not_in_cart:
            return {'error': 'no_coupon'}

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    sales_coupon_type_id = fields.Many2one('sales.coupon.type', 'Sales Coupon Type')
    sale_coupon_id = fields.Many2one('sales.coupon', 'Sales Coupon', readonly=True)
    coupon_code = fields.Many2one('sales.coupon', 'Sales Coupon Code', readonly=True)

    @api.v7
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, context=context)
        product_coupon_ids = self.pool.get('product.product').browse(cr, uid, product)
        res['value'].update({'sales_coupon_type_id': product_coupon_ids.product_tmpl_id.product_coupon_type.id})
        return res

    @api.multi
    def _create_coupon(self):
        coupon_manager_obj = self.env['sales.coupon']
        for line in self:
            sales_coupon_ids = [sales_coupon.id for sales_coupon in line.sales_coupon_type_id]
            if sales_coupon_ids and not line.coupon_code:
                coupon_manager_obj.create({
                    'partner_id': line.order_id.partner_id.id,
                    'coupon_type': sales_coupon_ids[0],
                    'product_id': line.product_id.id,
                    'validity': line.sales_coupon_type_id.validity_use,
                    'expiration_date': line.sales_coupon_type_id.expiration_date,
                    'expiration_use': line.sales_coupon_type_id.expiration_use,
                    'order_line_id': line.id,
                })
                coupon_code = coupon_manager_obj.search([('order_line_id', '=' ,line.id)])
                self.write({'sale_coupon_id': coupon_code.id })
        return True

    @api.v7
    def unlink(self, cr, uid, ids, context=None):
        so_line_obj = self.pool['sale.order.line']
        so_line=so_line_obj.browse(cr, uid, ids, context)
        if so_line.coupon_code:
            get_lines = so_line_obj.search(cr, uid, [('order_id', '=', so_line.order_id.id),('coupon_code', '=', so_line.coupon_code.id)], context=context)
            ids = get_lines
        return super(sale_order_line, self).unlink(cr, uid, ids, context)

    @api.one
    def button_confirm(self):
        res = super(sale_order_line, self).button_confirm()
        self._create_coupon()
        return res

class product_template(models.Model):
    _inherit = 'product.template'

    product_coupon_type = fields.Many2one('sales.coupon.type', 'Coupon Type')
