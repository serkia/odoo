from openerp.addons.web import http
from openerp.addons.web.http import request

class Website_coupon(http.Controller):
    @http.route(['/shop/apply_coupon'], type='json', auth="public", website=True)
    def shop_apply_coupon(self, promo, **post):
        order = request.website.sale_get_order()
        coupon_sale = request.env['sale.order'].apply_coupon(promo, order)
        return coupon_sale
