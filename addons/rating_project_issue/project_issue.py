# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ProjectIssue(models.Model):
    _name = "project.issue"
    _inherit = ['project.issue', 'rating.mixin']

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            template = self.env['project.task.type'].browse(vals.get('stage_id')).template_id
            if template.id:
                self.send_request(template)
        return super(ProjectIssue, self).write(vals)


class Project(models.Model):
    _inherit = "project.project"

    @api.multi
    def _get_total_happy_issue(self):
        happy = rated_issues = 0
        issue_obj = self.env['project.issue']
        project_issue = issue_obj.search([('project_id','=', self.id)])
        for issue in project_issue:
            # get last rating of issue
            rating = self.env['rating.rating'].search([('res_id', '=', issue.id), ('res_model', '=', 'project.issue')], limit=1)
            if rating.state:
                rated_issues += 1
                if rating.state == 'great':
                    happy += 1
        return rated_issues, happy

    @api.multi
    def _get_happy_customer_activity(self):
        res = super(Project, self)._get_happy_customer_activity()
        if self.use_issues and self.use_tasks:
            result = res + [self._get_total_happy_issue()]
        elif self.use_issues and not self.use_tasks:
            result = [self._get_total_happy_issue()]
        else:
            result = res
        return result

    @api.multi
    def action_view_rating(self):
        action = self.env['ir.actions.act_window'].for_xml_id('rating', 'action_view_rating')
        issues = self.env['project.issue'].search([('project_id', 'in', self.ids)])
        issue_domain = ['&', ('res_id', 'in', issues.ids), ('res_model', '=', 'project.issue')]
        if self.use_issues and self.use_tasks:
            domain = ['|'] + issue_domain + ['&', ('res_id', 'in', self.tasks.ids), ('res_model', '=', 'project.task')]
        elif self.use_issues and not self.use_tasks:
            domain = issue_domain
        else:
            return super(Project, self).action_view_rating()
        return dict(action, domain=domain)

    @api.multi
    def action_rating_issue(self):
        action = self.env['ir.actions.act_window'].for_xml_id('rating', 'action_view_rating')
        issues = self.env['project.issue'].search([('project_id', 'in', self.ids)])
        return dict(action, domain=[('res_id', 'in', issues.ids), ('res_model', '=', 'project.issue')])

    @api.multi
    def _percentage_count_issue(self):
        for record in self:
            rated_issues, happy = record._get_total_happy_issue()
            record.percent_happy_issue = ((happy*100) / rated_issues) if happy > 0 else 0

    @api.multi
    def _display_happy_customer(self):
        for record in self:
            record.is_visible_happy_customer = record.use_tasks if record.use_tasks else record.use_issues

    percent_happy_issue = fields.Integer(compute='_percentage_count_issue', string='% Happy')
