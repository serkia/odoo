# -*- coding: utf-'8' "-*-"

from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.osv import osv
from openerp.tools.float_utils import float_compare
from openerp.tools.translate import _

import logging
import pprint

_logger = logging.getLogger(__name__)


class TransferPaymentAcquirer(osv.Model):
    _inherit = 'payment.acquirer'

    def _format_transfer_data(self, cr, uid, context=None):
        bank_ids = [bank.id for bank in self.pool['res.users'].browse(cr, uid, uid, context=context).company_id.bank_ids]
        # filter only bank accounts marked as visible
        bank_ids = self.pool['res.partner.bank'].search(cr, uid, [('id', 'in', bank_ids), ('footer', '=', True)], context=context)
        accounts = self.pool['res.partner.bank'].name_get(cr, uid, bank_ids, context=context)
        bank_title = _('Bank Accounts') if len(accounts) > 1 else _('Bank Account')
        bank_accounts = ''.join(['<ul>'] + ['<li>%s</li>' % name for id, name in accounts] + ['</ul>'])
        post_msg = '''<div>
<h3>Please use the following transfer details</h3>
<h4>%(bank_title)s</h4>
%(bank_accounts)s
<h4>Communication</h4>
<p>Please use the order name as communication reference.</p>
</div>''' % {
            'bank_title': bank_title,
            'bank_accounts': bank_accounts,
        }
        return post_msg

    def create(self, cr, uid, values, context=None):
        """ Hook in create to create a default post_msg. This is done in create
        to have access to the name and other creation values. If no post_msg
        or a void post_msg is given at creation, generate a default one. """
        if values.get('name') == 'transfer' and not values.get('post_msg'):
            values['post_msg'] = self._format_transfer_data(cr, uid, context=context)
        return super(TransferPaymentAcquirer, self).create(cr, uid, values, context=context)

