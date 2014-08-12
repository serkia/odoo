from openerp.osv import osv
from openerp import fields, api
import time
import datetime

AVAILABLE_RATIO = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]


class crm_case_section(osv.osv):
    _inherit = "crm.case.section"

    ratio = fields.Float(string='Ratio')
    filter_ids = fields.Many2many('ir.filters', string='Filters')
    lead_ids = fields.One2many('crm.lead', 'section_id', string='Leads')


class res_users(osv.Model):
    _inherit = 'res.users'

    def _date_to_string(self, value):  # how can I do something else ?
        return time.mktime(datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").timetuple())

    @api.one
    def _count_leads(self):
        self.leads_count = self.lead_ids and sum(map(lambda x: 1, self.lead_ids)) or 0

    @api.one
    def _count_new_leads(self):
        self.new_leads_count = 0
        now = self._date_to_string(fields.Datetime.now())
        for lead in self.lead_ids:
            if now - self._date_to_string(lead.create_date) < 60 * 60 * 24 * 7:  # 7 days
                self.new_leads_count += 1

    ratio = fields.Selection(AVAILABLE_RATIO, string='Ratio', default='2')
    filter_ids = fields.Many2many('ir.filters', strong='Filters')
    lead_ids = fields.One2many('crm.lead', 'user_id', string='Leads')
    new_leads_count = fields.Integer(compute='_count_new_leads')
    leads_count = fields.Integer(compute='_count_leads')
