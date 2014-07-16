# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    template_id = fields.Many2one('email.template', string='Email Template For task',
                                    help="Select an email template. An email will be sent to the customer when the task reach this step.")


class Task(models.Model):
    _name = 'project.task'
    _inherit = ['project.task', 'rating.mixin']

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            template = self.env['project.task.type'].browse(vals.get('stage_id')).template_id
            if template.id:
                self.send_request(template)
        return super(Task, self).write(vals)


class Project(models.Model):
    _inherit = "project.project"

    @api.multi
    def action_rating_task(self):
        action = self.env['ir.actions.act_window'].for_xml_id('rating', 'action_view_rating')
        return dict(action, domain=[('res_id', 'in', self.tasks.ids), ('res_model', '=', 'project.task')])

    @api.multi
    def action_view_rating(self):
        return self.action_rating_task()

    @api.multi
    def _get_total_happy_task(self):
        happy = rated_tasks = 0
        for task in self.tasks:
            # get last rating of task
            rating = self.env['rating.rating'].search([('res_id', '=', task.id), ('res_model', '=', 'project.task')], limit=1)
            if rating.state:
                rated_tasks += 1
                if rating.state == 'great':
                    happy += 1
        return rated_tasks, happy

    @api.multi
    def _get_happy_customer_activity(self):
        return [self._get_total_happy_task()]

    @api.multi
    def _get_happy_customer(self):
        for record in self:
            total_happy = total_tasks = 0
            for activity in record._get_happy_customer_activity():
                rated_tasks, happy = activity
                total_tasks += rated_tasks
                total_happy += happy
            record.happy_customer = ((total_happy*100) / total_tasks) if total_happy > 0 else 0

    @api.multi
    def _percentage_count_task(self):
        for record in self:
            rated_tasks, happy = record._get_total_happy_task()
            record.percent_happy_task = ((happy*100) / rated_tasks) if happy > 0 else 0

    @api.multi
    def _display_happy_customer(self):
        for record in self:
            record.is_visible_happy_customer = record.use_tasks

    percent_happy_task = fields.Integer(compute='_percentage_count_task', string='% Happy')
    happy_customer = fields.Integer(compute="_get_happy_customer", string="% Happy")
    is_visible_happy_customer = fields.Boolean(compute="_display_happy_customer", string="Is Visible")
