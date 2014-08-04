import calendar
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import json

from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def _get_monthly_data(self):
        Holiday = self.env['hr.holidays']
        month_begin = date.today().replace(day=1)
        date_begin = (month_begin - relativedelta(months=self._period_number - 1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_end = month_begin.replace(day=calendar.monthrange(month_begin.year, month_begin.month)[1]).strftime(DEFAULT_SERVER_DATE_FORMAT)

        for department in self:
            domain_absence = [
                ('type', '=', 'remove'),
                ('department_id', '=', department.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('date_from', '>=', date_begin),
                ('date_to', '<=', date_end),]
            domain_request = [
                ('type', '=', 'add'),
                ('department_id', '=', department.id),
                ('state', 'not in', ['cancel', 'refuse']), 
                ('create_date', '>=', date_begin),
                ('create_date', '<=', date_end),]
            department.monthly_absence = json.dumps(self.__get_bar_values(Holiday, domain_absence, ['date_from'], 'date_from_count', 'date_from'))
            department.monthly_request = json.dumps(self.__get_bar_values(Holiday, domain_request, ['create_date'], 'create_date_count', 'create_date'))

    @api.multi
    def _leave_count(self):
        Holiday = self.env['hr.holidays']

        today_start = datetime.date.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        today_end = (datetime.date.today() + relativedelta(hours = 23, minutes=59, seconds=59)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        for department in self:
            department.leave_to_approve_count =  Holiday.search_count([
                ('department_id', '=', department.id), 
                ('state', '=', 'confirm'),
                ('type', '=', 'remove')])
            department.allocation_to_approve_count = Holiday.search_count([
                ('department_id', '=', department.id), 
                ('state', '=', 'confirm'),
                ('type', '=', 'add')])
            department.absence_of_today = Holiday.search_count([
                ('department_id', '=', department.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('date_from', '<=', today_end),
                ('date_to', '>=', today_start),
                ('type', '=', 'remove')])

    @api.multi
    def _get_total_employee(self):
        Employee = self.env['hr.employee']
        for department in self:
            department.total_employee = Employee.search_count([('department_id', '=', department.id)])

    absence_of_today = fields.Integer(compute='_leave_count', string='Absence by Today')
    leave_to_approve_count = fields.Integer(compute='_leave_count', string='Leave to Approve')
    allocation_to_approve_count = fields.Integer(compute='_leave_count', string='Allocation to Approve')
    total_employee = fields.Integer(compute='_get_total_employee', string='Total Employee')
    monthly_absence = fields.Char(compute='_get_monthly_data', string="Monthly Absence")
    monthly_request = fields.Char(compute='_get_monthly_data', string='Monthly Allocation Request')
