# -*- coding: utf-8 -*-

import time
from openerp import fields, models,api
from openerp.tools import amount_to_text_en

class ReportVoucher(models.AbstractModel):
    _name = 'report.l10n_in_account_voucher.report_voucher'

    title = fields.Char("Title", compute='_compute_get_title')
    debit = fields.Float("Debit", compute='_compute_debit')
    credit = fields.Float("Credit", compute='_compute_credit')

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

    def convert(self, amount, cur):
        return amount_to_text_en.amount_to_text(amount, 'en', cur)

    def _compute_get_title(self):
        title = ''
        if self.type:
            title = self.type[0].swapcase() + self.type[1:] + " Voucher"
        return title

    def _compute_debit(self):
        return sum(self.move_ids.debit) or 0.0

    def _compute_credit(self):
        return sum(self.move_ids.credit) or 0.0

    @api.model
    def _get_ref(self, voucher_id, move_ids):
        voucher = self.env['account.voucher.line'].search([('partner_id', '=', move_ids.partner_id.id), ('voucher_id', '=', voucher_id)])
        if voucher:
            return voucher[0].name

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
