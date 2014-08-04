import calendar
from datetime import date
from dateutil.relativedelta import relativedelta
import json

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def _get_monthly_expense_amount(self):
        Expense = self.env['hr.expense.expense']
        month_begin = date.today().replace(day=1)
        date_begin = (month_begin - relativedelta(months=self._period_number - 1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_end = month_begin.replace(day=calendar.monthrange(month_begin.year, month_begin.month)[1]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        for department in self:
            domain = [('department_id', '=', department.id),
                ('date', '>=', date_begin),
                ('date', '<=', date_end),
                ('state', '!=', 'cancelled')]
            department.monthly_expense_amount = json.dumps(self.__get_bar_values(Expense, domain, ['amount', 'date'], 'amount', 'date'))

    @api.multi
    def _expense_to_approve_count(self):
        Expense = self.env['hr.expense.expense']
        for department in self:
            department.expense_to_approve_count =  Expense.search_count([
                ('department_id', '=', department.id), ('state', '=', 'confirm')])

    expense_to_approve_count = fields.Integer(compute='_expense_to_approve_count', string='Expenses to Approve')
    monthly_expense_amount = fields.Char(compute='_get_monthly_expense_amount', string='Monthly Expenses')
