from openerp import models, fields, api

class hr_department(models.Model):
    _inherit = 'hr.department'

    @api.multi
    def _new_applicant_count(self):
        Applicant = self.env['hr.applicant']
        for department in self:
            department.new_applicant_count = Applicant.search_count([('department_id', '=', department.id), ('stage_id.sequence', '<=', '1')])

    @api.multi
    def _get_employee_stats(self):
        Job = self.env['hr.job']
        for department in self:
            res = Job.read_group([('department_id', '=', department.id)],
                ['no_of_hired_employee', 'no_of_recruitment', 'department_id'], 'department_id')
            department.new_hired_employee = res and res[0]['no_of_hired_employee'] or 0
            department.expected_employee = res and res[0]['no_of_recruitment'] or 0

    new_applicant_count = fields.Integer(compute='_new_applicant_count', string='New Applicant')
    new_hired_employee = fields.Integer(compute='_get_employee_stats', string='New Hired Employee')
    expected_employee = fields.Integer(compute='_get_employee_stats', string='Expected Employee')
