import datetime
from dateutil.relativedelta import relativedelta

from openerp.tests import common
from openerp.exceptions import AccessError, ValidationError, Warning
from openerp.tools import mute_logger

class TestSaleCoupon(common.TransactionCase):

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_sale_coupon_type(self):

        # Usefull models
        sale_obj = self.env['sale.order']
        sale_order_line = self.env['sale.order.line']
        sale_coupon_obj = self.env['sales.coupon']
        sale_coupon_type_obj = self.env['sales.coupon.type']
        product_obj = self.env['product.product']
        partner_obj = self.env['res.partner']

        #Case 1
        # create Sales Coupon type wit Expiration Date
        test_coupon_type1 = sale_coupon_type_obj.create({
            'name': 'TestCoupon1',
            'validity_use': 'expiration_date',
            'expiration_date': datetime.datetime.now() + relativedelta(days=1),
            'expiration_use': 0,
        })

        # create product with coupon Type
        test_product1 = product_obj.create({
            'name': 'National Conference',
            'type': 'service',
            'product_coupon_type': test_coupon_type1.id,
        })

        # create partner for sale order.
        partner_id = partner_obj.create({
            'name': 'Test Customer',
            'email': 'testcustomer@test.com',
        })

        # In order to test create sale order and confirmed it.
        order_id1 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product1.id})]
        })
        order_id1.action_button_confirm()
        # on Confirm SO it creates a sale Coupon with unique Coupon Code
        for order_line in order_id1.order_line:
            code = order_line.sale_coupon_id.code
            assert code, "Coupon Code: Creation of Coupon Code failed."

        order_id2 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product1.id})]
        })

        order_id2.apply_coupon(order_id1.order_line.sale_coupon_id.code, order_id2)
        order_id2.action_button_confirm()
        self.assertEqual(order_id2.amount_untaxed, 0.0, 'Coupon Code: Coupon Code not Apply')

        # Case 2
        # Create coupon with Expiration use
        test_coupon_type2 = sale_coupon_type_obj.create({
            'name': 'TestCoupon1',
            'validity_use': 'expiration_use',
            'expiration_date': datetime.datetime.now(),
            'expiration_use': 2,
        })

        # create product with coupon Type
        test_product2 = product_obj.create({
            'name': 'Training',
            'type': 'service',
            'product_coupon_type': test_coupon_type2.id,
        })

        order_id3 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product2.id})]
        })

        order_id3.action_button_confirm()
        # on Confirm SO it creates a sale Coupon with unique Coupon Code
        for order_line in order_id3.order_line:
            code = order_line.sale_coupon_id.code
            assert code, "Coupon Code: Creation of Coupon Code failed."

        order_id4 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product2.id})]
        })

        order_id4.apply_coupon(order_id3.order_line.sale_coupon_id.code, order_id4)
        order_id4.action_button_confirm()
        self.assertEqual(order_id4.amount_untaxed, 0.0, 'Coupon Code: Coupon Code not Apply')

        order_id5 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product2.id})]
        })

        order_id5.apply_coupon(order_id3.order_line.sale_coupon_id.code, order_id5)
        order_id5.action_button_confirm()
        self.assertEqual(order_id5.amount_untaxed, 0.0, 'Coupon Code: Coupon Code not Apply')

        order_id6 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product2.id})]
        })
        order_id6.apply_coupon(order_id3.order_line.sale_coupon_id.code, order_id6)
        order_id6.action_button_confirm()
        self.assertEqual(order_id6.amount_untaxed, 1.0, 'Coupon Code: Coupon Code not Apply')

        #Case 3 when multiple products in cart
        order_id7 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product1.id}),(0,0,{'product_id': test_product2.id})]
        })
        order_id7.apply_coupon(order_id1.order_line.sale_coupon_id.code, order_id7)
        order_id7.action_button_confirm()
        self.assertEqual(order_id7.amount_untaxed, 1.0, 'Coupon Code: Coupon Code not Apply')

        # Case 4 when multiple Quantity of same product
        order_id8 = sale_obj.create({
            'partner_id': partner_id.id,
            'date_order': datetime.datetime.now(),
            'order_line': [(0,0,{'product_id': test_product1.id, 'product_uom_qty': 5})]
        })
        order_id8.apply_coupon(order_id1.order_line.sale_coupon_id.code, order_id8)
        order_id8.action_button_confirm()
        self.assertEqual(order_id8.amount_untaxed, 4.0, 'Coupon Code: Coupon Code not Apply')
