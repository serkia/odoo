from datetime import date, datetime, timedelta
from openerp import tools
from openerp.addons.event.event import event_event as Event
from openerp.osv import fields, osv
from openerp.tools.translate import _

class sale_order_line(osv.Model):
    _inherit = 'sale.order.line'
    _columns = {
        'membership_start_date': fields.date('Membership Start Date', help='Date from which membership becomes active.'),
    }
    _defaults = {
        'membership_start_date': fields.datetime.now()
    }

    def _create_membership_line(self, cr, uid, ids, context=None):
        membership_line_obj = self.pool.get('membership.membership_line')
        for line in self.browse(cr, uid, ids, context=None):
            if line.product_id.membership:
                end_date = (datetime.strptime(line.membership_start_date,tools.DEFAULT_SERVER_DATE_FORMAT).date()) + (timedelta(int(line.product_id.membership_duration)*365/12))
                membership_line_obj.create(cr, uid, {
                    'partner': line.order_partner_id.id,
                    'membership_id': line.product_id.id,
                    'member_price': line.price_unit,
                    'date_from': line.membership_start_date,
                    'date_to': end_date,
                    'state': 'waiting',
                    'sale_order_line_id': line.id
                }, context=context)
        return True

    def button_confirm(self, cr, uid, ids, context=None):
        res = super(sale_order_line, self).button_confirm(cr, uid, ids, context=context)
        self._create_membership_line(cr, uid, ids, context=context)
        return res

    def invoice_line_create(self, cr, uid, ids, context=None):
        membership_line_obj = self.pool.get('membership.membership_line')
        res = []
        for line_id in ids:
            invoice_line_ids = super(sale_order_line, self).invoice_line_create(cr, uid, [line_id], context=context)
            res += invoice_line_ids
            if line_id:
                membership_line_ids = membership_line_obj.search(cr, uid, [('sale_order_line_id', '=' , line_id)])
            if membership_line_ids and invoice_line_ids:
                membership_line_obj.write(cr, uid, membership_line_ids, {
                    'date': fields.datetime.now(),
                    'account_invoice_line': invoice_line_ids[0],
                }, context=context)
        return res

class membership_line(osv.Model):
    '''Membership line'''
    _inherit = 'membership.membership_line'

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order line', readonly=True),
        'sale_order_id': fields.related('sale_order_line_id', 'order_id', type='many2one', relation='sale.order', string='Sale Order', readonly=True),
    }


class account_invoice_line(osv.Model):
    _inherit='account.invoice.line'

    def _prepare_domain_invoice_membeship(self, line):
        domain = super(account_invoice_line, self)._prepare_domain_invoice_membeship(line)
        return ['|', ('sale_order_line_id', '!=', False)] + domain
