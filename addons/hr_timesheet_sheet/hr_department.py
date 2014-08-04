import calendar
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def _get_monthly_timesheet_amount(self):
        Timesheet = self.env['hr_timesheet_sheet.sheet.day']
        month_begin = date.today().replace(day=1)
        date_begin = (month_begin - relativedelta(months=self._period_number - 1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_end = month_begin.replace(day=calendar.monthrange(month_begin.year, month_begin.month)[1]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        for department in self:
            domain = [('sheet_id.department_id', '=', department.id), ('name', '>=', date_begin), ('name', '<=', date_end)]
            department.monthly_timesheet_amount = json.dumps(self.__get_bar_values(Timesheet, domain, ['total_timesheet', 'name'], 'total_timesheet', 'name'))

    @api.multi
    def _timesheet_to_approve_count(self):
        Timesheet = self.env['hr_timesheet_sheet.sheet']
        for department in self:
            department.timesheet_to_approve_count = Timesheet.search_count(
                [('department_id', '=', department.id), ('state', '=', 'confirm')])


    timesheet_to_approve_count = fields.Integer(compute='_timesheet_to_approve_count', string='Timesheet to Approve')
    monthly_timesheet_amount = fields.Char(compute='_get_monthly_timesheet_amount', string='Monthly Timesheet Amount')
