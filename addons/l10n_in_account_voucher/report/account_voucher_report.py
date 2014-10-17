# -*- coding: utf-8 -*-

import time
from openerp import fields, models, api
from openerp.tools import amount_to_text_en

class ReportVoucher(models.AbstractModel):
    _name = 'report.l10n_in_account_voucher.report_voucher'

    @api.model
    def render_html(self, ids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('l10n_in_account_voucher.report_voucher')
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': self.env['account.voucher'].search([('id', 'in', ids)]),
            'time': time,
            'convert': self.convert,
            'get_title': self.get_title,
            'debit': self.debit,
            'credit': self.credit,
            'get_ref': self._get_ref
        }
        return report_obj.render('l10n_in_account_voucher.report_voucher', docargs)

    def get_title(self, type):
        title = ''
        if type:
            title = type[0].swapcase() + type[1:] + " Voucher"
        return title

    def debit(self, move_ids):
        for move in move_ids:
            debit += move.debit
        return debit or 0.0

    def credit(self, move_ids):
        for move in move_ids:
            credit += move.credit
        return credit or 0.0

    @api.model
    def _get_ref(self, voucher_id, move_ids):
        voucher = self.env['account.voucher.line'].search([('partner_id', '=', move_ids.partner_id.id), ('voucher_id', '=', voucher_id)])
        if voucher:
            return voucher[0].name

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
