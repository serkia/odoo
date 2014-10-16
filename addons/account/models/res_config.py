# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

import time
import datetime
from dateutil.relativedelta import relativedelta

import openerp
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
from openerp import models, fields, api, _

class account_config_settings(models.TransientModel):
    _name = 'account.config.settings'
    _inherit = 'res.config.settings'


    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id.id)
    has_default_company = fields.Boolean(string='Has default company', readonly=True,
        default=lambda self: self._default_has_default_company())
    expects_chart_of_accounts = fields.Boolean(related='company_id.expects_chart_of_accounts',
        string='This company has its own chart of accounts',
        help='Check this box if this company is a legal entity.')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', required=True,
        string='Default company currency', help="Main currency of the company.")
    paypal_account = fields.Char(related='company_id.paypal_account', size=128, string='Paypal account',
        help="""Paypal account (email) for receiving online payments (credit card, etc.) 
             If you set a paypal account, the customer  will be able to pay your invoices or quotations 
             with a button \"Pay with  Paypal\" in automated emails or through the Odoo portal.""")
    company_footer = fields.Text(related='company_id.rml_footer', string='Bank accounts footer preview',
        readonly=True, help="Bank accounts as printed in the footer of each printed document")

    has_chart_of_accounts = fields.Boolean(string='Company has a chart of accounts')
    chart_template_id = fields.Many2one('account.chart.template', string='Template',
        domain="[('visible','=', True)]")
    code_digits = fields.Integer(string='# of Digits', help="No. of digits to use for account code")
    tax_calculation_rounding_method = fields.Selection(
        [
        ('round_per_line', 'Round calculation of taxes per line'),
        ('round_globally', 'Round globally calculation of taxes '),
        ], related='company_id.tax_calculation_rounding_method', string='Tax calculation rounding method',
        help="""If you select 'Round per line' : for each tax, the tax amount will first be 
             computed and rounded for each PO/SO/invoice line and then these rounded amounts will be summed, 
             leading to the total amount for that tax. If you select 'Round globally': for each tax, 
             the tax amount will be computed for each PO/SO/invoice line, then these amounts will be 
             summed and eventually this total tax amount will be rounded. If you sell with tax included, 
             you should choose 'Round per line' because you certainly want the sum of your tax-included line 
             subtotals to be equal to the total amount with taxes.""")
    sale_tax = fields.Many2one('account.tax.template', string='Default sale tax')
    purchase_tax = fields.Many2one('account.tax.template', string='Default purchase tax')
    sale_tax_rate = fields.Float(string='Sales tax (%)')
    purchase_tax_rate = fields.Float(string='Purchase tax (%)')
    complete_tax_set = fields.Boolean(string='Complete set of taxes', 
        help='''This boolean helps you to choose if you want to propose to the user to encode 
             the sales and purchase rates or use the usual m2o fields. This last choice assumes that 
             the set of tax defined for the chosen template is complete''')

    has_fiscal_year = fields.Boolean(string='Company has a fiscal year')
    date_start = fields.Date(string='Start date', required=True)
    date_stop = fields.Date(string='End date', required=True)
    period = fields.Selection([('month', 'Monthly'), ('3months','3 Monthly')], string='Periods', required=True)

    sale_journal_id = fields.Many2one('account.journal', string='Sale journal')
    sale_sequence_prefix = fields.Char(related='sale_journal_id.sequence_id.prefix', string='Invoice sequence')
    sale_sequence_next = fields.Integer(related='sale_journal_id.sequence_id.number_next',
        string='Next invoice number')
    sale_refund_journal_id = fields.Many2one('account.journal', string='Sale refund journal')
    sale_refund_sequence_prefix = fields.Char(related='sale_refund_journal_id.sequence_id.prefix',
        string='Credit note sequence')
    sale_refund_sequence_next = fields.Integer(related='sale_refund_journal_id.sequence_id.number_next',
        string='Next credit note number')
    purchase_journal_id = fields.Many2one('account.journal', string='Purchase journal')
    purchase_sequence_prefix = fields.Char(related='purchase_journal_id.sequence_id.prefix',
        string='Supplier invoice sequence')
    purchase_sequence_next = fields.Integer(related='purchase_journal_id.sequence_id.number_next',
        string='Next supplier invoice number')
    purchase_refund_journal_id = fields.Many2one('account.journal', string='Purchase refund journal')
    purchase_refund_sequence_prefix = fields.Char(related='purchase_refund_journal_id.sequence_id.prefix',
        string='Supplier credit note sequence')
    purchase_refund_sequence_next = fields.Integer(related='purchase_refund_journal_id.sequence_id.number_next',
        string='Next supplier credit note number')

    module_account_check_writing = fields.Boolean(string='Pay your suppliers by check',
        help='This allows you to check writing and printing.\n'
             '-This installs the module account_check_writing.')
    module_account_accountant = fields.Boolean(string='Full accounting features: journals, legal statements, chart of accounts, etc.',
        help="""If you do not check this box, you will be able to do invoicing & payments, 
             but not accounting (Journal Items, Chart of  Accounts, ...)""")
    module_account_asset = fields.Boolean(string='Assets management',
        help='This allows you to manage the assets owned by a company or a person.\n'
             'It keeps track of the depreciation occurred on those assets, and creates account move for those depreciation lines.\n'
             '-This installs the module account_asset. If you do not check this box, you will be able to do invoicing & payments, '
             'but not accounting (Journal Items, Chart of Accounts, ...)')
    module_account_budget = fields.Boolean(string='Budget management',
        help='This allows accountants to manage analytic and crossovered budgets. '
             'Once the master budgets and the budgets are defined, '
             'the project managers can set the planned amount on each analytic account.\n'
             '-This installs the module account_budget.')
    module_account_payment = fields.Boolean(string='Manage payment orders',
        help='This allows you to create and manage your payment orders, with purposes to \n'
             '* serve as base for an easy plug-in of various automated payment mechanisms, and \n'
             '* provide a more efficient way to manage invoice payments.\n'
             '-This installs the module account_payment.' )
    module_account_voucher = fields.Boolean(string='Manage customer payments',
        help='This includes all the basic requirements of voucher entries for bank, cash, sales, purchase, expense, contra, etc.\n'
             '-This installs the module account_voucher.')
    module_account_followup = fields.Boolean(string='Manage customer payment follow-ups',
        help='This allows to automate letters for unpaid invoices, with multi-level recalls.\n'
             '-This installs the module account_followup.')
    module_product_email_template = fields.Boolean(string='Send products tools and information at the invoice confirmation',
        help='With this module, link your products to a template to send complete information and tools to your customer.\n'
             'For instance when invoicing a training, the training agenda and materials will automatically be send to your customers.')
    module_account_bank_statement_import_ofx = fields.Boolean(string='Import of Bank Statements in .OFX Format',
        help='Get your bank statements from you bank and import them in Odoo in .OFX format.\n'
            '-that installs the module account_bank_statement_import.')
    module_account_bank_statement_import_qif = fields.Boolean(string='Import of Bank Statements in .QIF Format.',
        help='Get your bank statements from you bank and import them in Odoo in .QIF format.\n'
            '-that installs the module account_bank_statement_import_qif.')
    group_proforma_invoices = fields.Boolean(string='Allow pro-forma invoices',
        implied_group='account.group_proforma_invoices',
        help="Allows you to put invoices in pro-forma state.")
    default_sale_tax = fields.Many2one('account.tax', string='Default sale tax',
        help="This sale tax will be assigned by default on new products.")
    default_purchase_tax = fields.Many2one('account.tax', string='Default purchase tax',
        help="This purchase tax will be assigned by default on new products.")
    decimal_precision = fields.Integer(string='Decimal precision on journal entries',
        help="""As an example, a decimal precision of 2 will allow journal entries  like: 9.99 EUR, 
             whereas a decimal precision of 4 will allow journal  entries like: 0.0231 EUR.""")
    group_multi_currency = fields.Boolean(string='Allow multi currencies',
        implied_group='base.group_multi_currency',
        help="Allows you multi currency environment")
    group_analytic_accounting = fields.Boolean(string='Analytic accounting',
        implied_group='analytic.group_analytic_accounting',
        help="Allows you to use the analytic accounting.")
    group_check_supplier_invoice_total = fields.Boolean(string='Check the total of supplier invoices', 
        implied_group="account.group_supplier_inv_check_total")
    income_currency_exchange_account_id = fields.Many2one('account.account',
        related='company_id.income_currency_exchange_account_id',
        string="Gain Exchange Rate Account", 
        domain="[('type', '=', 'other'), ('deprecated', '=', False)]")
    expense_currency_exchange_account_id = fields.Many2one('account.account',
        related='company_id.expense_currency_exchange_account_id',
        string="Loss Exchange Rate Account",
        domain="[('type', '=', 'other'), ('deprecated', '=', False)]")


    @api.multi
    def onchange_company_id(self, company_id):
        res = super(account_config_settings, self).onchange_company_id(company_id)
        if company_id:
            company = self.env['res.company'].browse(company_id)
            res['value'].update({'income_currency_exchange_account_id': company.income_currency_exchange_account_id and company.income_currency_exchange_account_id.id or False, 
                                 'expense_currency_exchange_account_id': company.expense_currency_exchange_account_id and company.expense_currency_exchange_account_id.id or False})
        else: 
            res['value'].update({'income_currency_exchange_account_id': False, 
                                 'expense_currency_exchange_account_id': False})
        return res


    @api.model
    def _default_has_default_company(self):
        count = self.env['res.company'].search_count([])
        return bool(count == 1)

    @api.model
    def _get_default_fiscalyear_data(self, company_id):
        """Compute default period, starting and ending date for fiscalyear
        - if in a fiscal year, use its period, starting and ending date
        - if past fiscal year, use its period, and new dates [ending date of the latest +1 day ; ending date of the latest +1 year]
        - if no fiscal year, use monthly, 1st jan, 31th dec of this year
        :return: (date_start, date_stop, period) at format DEFAULT_SERVER_DATETIME_FORMAT
        """
        FiscalyearObj = self.env['account.fiscalyear']
        fiscalyear_ids = FiscalyearObj.search(
                [('date_start', '<=', time.strftime(DF)), ('date_stop', '>=', time.strftime(DF)),
                 ('company_id', '=', company_id)])
        if fiscalyear_ids:
            # is in a current fiscal year, use this one
            fiscalyear = fiscalyear_ids[0]
            if len(fiscalyear.period_ids) == 5:  # 4 periods of 3 months + opening period
                period = '3months'
            else:
                period = 'month'
            return (fiscalyear.date_start, fiscalyear.date_stop, period)
        else:
            past_fiscalyear_ids = FiscalyearObj.search(
                [('date_stop', '<=', time.strftime(DF)), ('company_id', '=', company_id)])
            if past_fiscalyear_ids:
                # use the latest fiscal, sorted by (start_date, id)
                latest_year = past_fiscalyear_ids[-1]
                latest_stop = datetime.datetime.strptime(latest_year.date_stop, DF)
                if len(latest_year.period_ids) == 5:
                    period = '3months'
                else:
                    period = 'month'
                return ((latest_stop+datetime.timedelta(days=1)).strftime(DF), latest_stop.replace(year=latest_stop.year+1).strftime(DF), period)
            else:
                return (time.strftime('%Y-01-01'), time.strftime('%Y-12-31'), 'month')


    @api.model
    def create(self, values):
        rec = super(account_config_settings, self).create(values)
        # Hack: to avoid some nasty bug, related fields are not written upon record creation.
        # Hence we write on those fields here.
        vals = {}
        for fname, field in self._fields.iteritems():
            if getattr(field, 'related') and fname in values:
                vals[fname] = values[fname]
        rec.write(vals)
        return rec

    @api.multi
    def onchange_company_id(self, company_id):
        # update related fields
        values = {}
        values['currency_id'] = False
        if company_id:
            company = self.env['res.company'].browse(company_id)
            has_chart_of_accounts = company_id not in self.env['account.installer'].get_unconfigured_cmp()
            fiscalyear_count = self.env['account.fiscalyear'].search_count(
                [('date_start', '<=', time.strftime('%Y-%m-%d')), ('date_stop', '>=', time.strftime('%Y-%m-%d')),
                 ('company_id', '=', company_id)])
            date_start, date_stop, period = self._get_default_fiscalyear_data(company_id)
            values = {
                'expects_chart_of_accounts': company.expects_chart_of_accounts,
                'currency_id': company.currency_id.id,
                'paypal_account': company.paypal_account,
                'company_footer': company.rml_footer,
                'has_chart_of_accounts': has_chart_of_accounts,
                'has_fiscal_year': bool(fiscalyear_count),
                'chart_template_id': False,
                'tax_calculation_rounding_method': company.tax_calculation_rounding_method,
                'date_start': date_start,
                'date_stop': date_stop,
                'period': period,
            }
            # update journals and sequences
            for journal_type in ('sale', 'sale_refund', 'purchase', 'purchase_refund'):
                for suffix in ('_journal_id', '_sequence_prefix', '_sequence_next'):
                    values[journal_type + suffix] = False

            for journal in self.env['account.journal'].search([('company_id', '=', company_id)]):
                if journal.type in ('sale', 'sale_refund', 'purchase', 'purchase_refund'):
                    values.update({
                        journal.type + '_journal_id': journal.id,
                        journal.type + '_sequence_prefix': journal.sequence_id.prefix,
                        journal.type + '_sequence_next': journal.sequence_id.number_next,
                    })
            # update taxes
            ir_values = self.env['ir.values']
            taxes_id = ir_values.get_default('product.product', 'taxes_id', company_id=company_id)
            supplier_taxes_id = ir_values.get_default('product.product', 'supplier_taxes_id', company_id=company_id)
            values.update({
                'default_sale_tax': isinstance(taxes_id, list) and taxes_id[0] or taxes_id,
                'default_purchase_tax': isinstance(supplier_taxes_id, list) and supplier_taxes_id[0] or supplier_taxes_id,
            })
        return {'value': values}

    @api.multi
    def onchange_chart_template_id(self, chart_template_id):
        tax_templ_obj = self.env['account.tax.template']
        res = {'value': {
            'complete_tax_set': False, 'sale_tax': False, 'purchase_tax': False,
            'sale_tax_rate': 15, 'purchase_tax_rate': 15,
        }}
        if chart_template_id:
            # update complete_tax_set, sale_tax and purchase_tax
            chart_template = self.env['account.chart.template'].browse(chart_template_id)
            res['value'].update({'complete_tax_set': chart_template.complete_tax_set})
            if chart_template.complete_tax_set:
                # default tax is given by the lowest sequence. For same sequence we will take the latest created as it will be the case for tax created while isntalling the generic chart of account
                sale_tax_ids = tax_templ_obj.search(
                    [("chart_template_id", "=", chart_template_id), ('type_tax_use', 'in', ('sale','all'))],
                    order="sequence, id desc")
                purchase_tax_ids = tax_templ_obj.search(
                    [("chart_template_id", "=", chart_template_id), ('type_tax_use', 'in', ('purchase','all'))],
                    order="sequence, id desc")
                res['value']['sale_tax'] = sale_tax_ids and sale_tax_ids[0] or False
                res['value']['purchase_tax'] = purchase_tax_ids and purchase_tax_ids[0] or False
            if chart_template.code_digits:
                res['value']['code_digits'] = chart_template.code_digits
        return res

    @api.multi
    def onchange_tax_rate(self, rate):
        return {'value': {'purchase_tax_rate': rate or False}}

    @api.multi
    def onchange_multi_currency(self, group_multi_currency):
        res = {}
        if not group_multi_currency:
            res['value'] = {'income_currency_exchange_account_id': False, 'expense_currency_exchange_account_id': False}
        return res
    
    @api.multi
    def onchange_start_date(self, start_date):
        if start_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = (start_date + relativedelta(months=12)) - relativedelta(days=1)
            return {'value': {'date_stop': end_date.strftime('%Y-%m-%d')}}
        return {}

    @api.multi
    def open_company_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configure your Company',
            'res_model': 'res.company',
            'res_id': self.company_id.id,
            'view_mode': 'form',
        }

    @api.multi
    def set_default_taxes(self):
        """ set default sale and purchase taxes for products """
        if self._uid != SUPERUSER_ID and not self.env['res.users'].has_group('base.group_erp_manager'):
            raise openerp.exceptions.AccessError(_("Only administrators can change the settings"))
        ir_values = self.env['ir.values']
        ir_values.sudo().set_default('product.product', 'taxes_id',
            self.default_sale_tax and [self.default_sale_tax.id] or False, company_id=self.company_id.id)
        ir_values.sudo().set_default('product.product', 'supplier_taxes_id',
            self.default_purchase_tax and [self.default_purchase_tax.id] or False, company_id=self.company_id.id)

    @api.multi
    def set_chart_of_accounts(self):
        """ install a chart of accounts for the given company (if required) """
        if self.chart_template_id:
            assert self.expects_chart_of_accounts and not self.has_chart_of_accounts
            wizard = self.env['wizard.multi.charts.accounts']
            wizard_id = wizard.create({
                'company_id': self.company_id.id,
                'chart_template_id': self.chart_template_id.id,
                'code_digits': self.code_digits or 6,
                'sale_tax': self.sale_tax.id,
                'purchase_tax': self.purchase_tax.id,
                'sale_tax_rate': self.sale_tax_rate,
                'purchase_tax_rate': self.purchase_tax_rate,
                'complete_tax_set': self.complete_tax_set,
                'currency_id': self.currency_id.id,
            }, context)
            wizard.execute([wizard_id])

    @api.multi
    def set_fiscalyear(self):
        """ create a fiscal year for the given company (if necessary) """
        if self.has_chart_of_accounts or self.chart_template_id:
            FiscalyearObj = self.env['account.fiscalyear']
            fiscalyear_count = FiscalyearObj.search_count(
                [('date_start', '<=', self.date_start), ('date_stop', '>=', self.date_stop),
                 ('company_id', '=', self.company_id.id)])
            if not fiscalyear_count:
                name = code = self.date_start[:4]
                if int(name) != int(self.date_stop[:4]):
                    name = self.date_start[:4] +'-'+ self.date_stop[:4]
                    code = self.date_start[2:4] +'-'+ self.date_stop[2:4]
                vals = {
                    'name': name,
                    'code': code,
                    'date_start': self.date_start,
                    'date_stop': self.date_stop,
                    'company_id': self.company_id.id,
                }
                fiscalyear_id = FiscalyearObj.create(vals)
                if self.period == 'month':
                    FiscalyearObj.create_period([fiscalyear_id])
                elif self.period == '3months':
                    FiscalyearObj.create_period3([fiscalyear_id])

    @api.model
    def get_default_dp(self, fields):
        dp = self.env['ir.model.data'].get_object('product','decimal_account')
        return {'decimal_precision': dp.digits}

    @api.multi
    def set_default_dp(self):
        dp = self.env['ir.model.data'].get_object('product','decimal_account')
        dp.write({'digits': self.decimal_precision})

    @api.multi
    def onchange_analytic_accounting(self, analytic_accounting):
        if analytic_accounting:
            return {'value': {
                'module_account_accountant': True,
                }}
        return {}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: