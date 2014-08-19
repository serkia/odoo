from openerp.osv import osv
from openerp import fields, api, models, SUPERUSER_ID
import time
import datetime
from openerp.tools.safe_eval import safe_eval

AVAILABLE_RATIO = [
    ('0', 'No ratio'),
    ('1', 'Very Low'),
    ('2', 'Low'),
    ('3', 'Normal'),
    ('4', 'High'),
    ('5', 'Very High'),
]

DOMAINS = [
    ('ir.filters', 'Filters'),
    ('res.partner', 'Customers'),
]


class crm_case_section(osv.osv):
    _inherit = "crm.case.section"

    @api.one
    def _count_leads(self):
        self.leads_count = self.lead_ids and sum(map(lambda x: 1, self.lead_ids)) or 0

    ratio = fields.Float(string='Ratio')
    filter_ids = fields.Many2many('ir.filters', string='Filters')
    lead_ids = fields.One2many('crm.lead', 'section_id', string='Leads')
    leads_count = fields.Integer(compute='_count_leads')
    maximum_section_leads = fields.Integer('Maximum leads')
    section_user_ids = fields.One2many('section.user', 'section_id', string='Salemen')

    def assign_leads(self, cr, uid, context=None):
        # loop on salesteams

        # Verifier/tester cette horreur

        filters_fields = ['domain']
        all_filters = self.pool["ir.filters"].search_read(cr, SUPERUSER_ID, fields=filters_fields, context=context)
        print 'filters', all_filters

        salesteams_fields = ['filter_ids', 'leads_count', 'maximum_section_leads']
        all_salesteams = self.search_read(cr, SUPERUSER_ID, fields=salesteams_fields, context=context)

        section_users_fields = ['section_domain', 'user_id', 'section_id', 'maximum_user_leads']
        all_section_users = self.pool['section.user'].search_read(cr, SUPERUSER_ID, fields=section_users_fields, context=context)

        # I would need all the fields of all leads...
        leads_fields = ['section_id', 'user_id']
        all_leads = self.pool["crm.lead"].search_read(cr, SUPERUSER_ID, fields=leads_fields, context=context)

        users_fields = ['leads_count']
        all_users = self.pool['res.users'].search_read(cr, SUPERUSER_ID, fields=users_fields, context=context)

        for lead in all_leads:
            if not lead['section_id'] and not lead['user_id']:
                print lead
                potential_salesteams = []
                for salesteam in all_salesteams:
                    filter_ids = salesteam['filter_ids']
                    filters = [safe_eval(f['domain']) for f in all_filters if f['id'] in filter_ids]
                    # flatten the list of filters
                    filters = [f for sublist in filters for f in sublist]
                    # should be done otherwise, it represents a lot of accesses to the db
                    domain = [('id', '=', lead['id'])] + filters
                    lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
                    if lead_fit:
                        potential_salesteams.append(salesteam)
                print 'potential_salesteams', potential_salesteams
                # need to decide what to do with the lead, because if a team has no filters, it potentially gets everything

                # self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead['id'], {'section_id': chosen_team_id}, context=context)
                # the chosen salesteams must be updated in the all_salesteam dict : lead_count += 1
                # the lead should be updated in the dict : section_id = chosen_team_id

        for salesteam in all_salesteams:
            domain = [('section_id', '=', salesteam['id'])]
            team_leads = [lead for lead in all_leads if lead['section_id'] == salesteam['id']]
            # need to decide which leads will be asigned, I first consider that's all of them



        # print "for1"
        # for team in self.search_read(cr, uid, fields=['filter_ids', 'leads_count', 'maximum_section_leads'], context=context):
        #     print 'team', team
        #     domain = team['filter_ids']
        #     # filters associated with the current team
        #     filters = self.pool["ir.filters"].search_read(cr, uid, domain=[('id', 'in', domain)], fields=['domain'], context=context)
        #     # making sure that the lead is not yet assigned
        #     print 'filters', filters
        #     domain = [('section_id', '=', False), ('user_id', '=', False)]
        #     for f in filters:
        #         domain.extend(safe_eval(f['domain']))
        #     print 'domain', domain
        #     potential_leads = self.pool["crm.lead"].search(cr, uid, domain, context=context)
        #     print potential_leads
        #     for lead_id in potential_leads:
        #         # assigning all potential_leads to the salesteam
        #         # todo: are the domains exclusive ?
        #         if team['leads_count'] < team['maximum_section_leads']:
        #             self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead_id, {'section_id': team['id']}, context=context)

        #     print "for2"
        #     for man in self.pool['section.user'].search_read(cr, SUPERUSER_ID, [('section_id', '=', team['id'])], fields=['section_domain', 'user_id', 'maximum_user_leads'], context=context):
        #         print 'man', man
        #         section_domain = man['section_domain']
        #         if section_domain:
        #             section_domain = safe_eval(man['section_domain'])
        #             filters = self.pool["ir.filters"].search_read(cr, SUPERUSER_ID, section_domain, fields=['domain'], context=context)
        #         else:
        #             filters = []

        #         # print 'section_domain', section_domain
        #         # filters = self.pool["ir.filters"].search_read(cr, SUPERUSER_ID, section_domain, fields=['domain'], context=context)

        #         # getting the filters on the salesman
        #         # filters = self.pool["ir.filters"].search_read(cr, SUPERUSER_ID, domain, fields= ['domain'], context=context)
        #         print 'filters', filters
        #         # making sure that the leads are in unassigned to a salesman and for this salesteam
        #         domain = [('section_id', '=', team['id']), ('user_id', '=', False)]
        #         for f in filters:
        #             domain.extend(safe_eval(f['domain']))
        #         print 'domain', domain
        #         potential_leads = self.pool["crm.lead"].search(cr, uid, domain, context=context)
        #         print potential_leads
        #         for lead_id in potential_leads:
        #             user = self.pool['res.users'].search_read(cr, SUPERUSER_ID, [('id', '=', man['user_id'][0])], fields=['leads_count'], context=context)
        #             print 'user', user
        #             if user[0]['leads_count'] < man['maximum_user_leads']:
        #                 self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead_id, {'user_id': man['id']}, context=context)


class res_users(osv.Model):
    _inherit = 'res.users'

    def _date_to_string(self, value):  # how can I do something else ?
        return time.mktime(datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").timetuple())  # server datetimeformat

    @api.one
    def _count_leads(self):
        self.leads_count = self.lead_ids and sum(map(lambda x: 1, self.lead_ids)) or 0

    @api.one
    def _count_new_leads(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=7)
        self.new_leads_count = self.lead_ids and sum(map(lambda x: 1 if (now - fields.Datetime.from_string(x.create_date)) < delta else 0, self.lead_ids)) or 0   # use timedelta

    # ratio = fields.Selection(AVAILABLE_RATIO, string='Ratio', default='0')
    # filter_ids = fields.Many2many('ir.filters', strong='Filters')
    lead_ids = fields.One2many('crm.lead', 'user_id', string='Leads')
    new_leads_count = fields.Integer(compute='_count_new_leads')
    leads_count = fields.Integer(compute='_count_leads')


class section_user(models.Model):

    _name = 'section.user'

    @api.one
    def _get_percentage(self):
        try:
            self.percentage_leads = 100 * self.user_id.leads_count / float(self.maximum_user_leads)
        except ZeroDivisionError:
            self.percentage_leads = 0.0

    section_id = fields.Many2one('crm.case.section', string='SaleTeam', required=True)
    user_id = fields.Many2one('res.users', string='Saleman', required=True)
    user_name = fields.Char(related='user_id.partner_id.display_name')
    # section_model = fields.Selection(DOMAINS, string='Filters', required=True)
    section_domain = fields.Char('Domain')
    maximum_user_leads = fields.Integer('Maximum leads')
    percentage_leads = fields.Float(compute='_get_percentage', string='Percentage leads')
