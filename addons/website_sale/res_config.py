from openerp import models, fields, api, _

class sales_coupon_config_settings(models.TransientModel):
    _inherit = 'sale.config.settings'

    module_website_sale_coupon = fields.Boolean(string='Allow presale voucher',
        help="To allow Coupon on selected products.")
