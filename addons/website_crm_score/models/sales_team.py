from openerp.osv import osv
from openerp import fields, api, models, SUPERUSER_ID
import time
import datetime
from openerp.tools.safe_eval import safe_eval
from random import randint

AVAILABLE_RATIO = [
    ('0', 'No ratio'),
    ('1', 'Very Low'),
    ('2', 'Low'),
    ('3', 'Normal'),
    ('4', 'High'),
    ('5', 'Very High'),
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

        def get_filters(filter_ids):
            filters = [safe_eval(f['domain']) for f in all_filters if f['id'] in filter_ids]
            # flatten the list of filters
            filters = [f for sublist in filters for f in sublist]
            return filters

        def list_to_dict_keys(d, l, v):
            for e in l:
                if e in d:
                    d[e].append(v)
                else:
                    d[e] = [v]


        filters_fields = ['domain']
        all_filters = self.pool["ir.filters"].search_read(cr, SUPERUSER_ID, fields=filters_fields, context=context)
        print 'filters', all_filters

        salesteams_fields = ['filter_ids', 'leads_count', 'maximum_section_leads']
        all_salesteams = self.search_read(cr, SUPERUSER_ID, fields=salesteams_fields, context=context)
        # casting the list into a dict to ease the access afterwards
        all_salesteams = {team['id']: team for team in all_salesteams}
        print 'all_salesteams', all_salesteams

        section_users_fields = ['section_domain', 'user_id', 'section_id', 'maximum_user_leads']
        all_section_users = self.pool['section.user'].search_read(cr, SUPERUSER_ID, fields=section_users_fields, context=context)

        # I would need all the fields of all leads...
        leads_fields = ['section_id', 'user_id']
        all_leads = self.pool["crm.lead"].search_read(cr, SUPERUSER_ID, fields=leads_fields, context=context)

        users_fields = ['leads_count']
        all_users = self.pool['res.users'].search_read(cr, SUPERUSER_ID, fields=users_fields, context=context)

        # lead assignement to salesteams

        # V1
        # for lead in all_leads:
        #     if not lead['section_id'] and not lead['user_id']:
        #         print lead
        #         potential_salesteams = []
        #         for salesteam in all_salesteams:
        #             filter_ids = salesteam['filter_ids']
        #             filters = get_filters(filter_ids)
        #             # should be done otherwise, it represents a lot of accesses to the db
        #             domain = [('id', '=', lead['id'])] + filters
        #             lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
        #             if lead_fit:
        #                 potential_salesteams.append(salesteam)
        #         print 'potential_salesteams', potential_salesteams
        #         # need to decide what to do with the lead, because if a team has no filters, it potentially gets everything

        #         # self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead['id'], {'section_id': chosen_team_id}, context=context)
        #         # the chosen salesteams must be updated in the all_salesteam dict : lead_count += 1
        #         # the lead should be updated in the dict : section_id = chosen_team_id

        # V2
        potential_salesteams_for_leads = {}
        for _, salesteam in all_salesteams.iteritems():
            filter_ids = salesteam['filter_ids']
            filters = get_filters(filter_ids)
            # should be done otherwise, it represents a lot of accesses to the db
            domain = [('section_id', '=', False), ('user_id', '=', False)] + filters
            lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
            if lead_fit:
                print 'salesteam', salesteam
                list_to_dict_keys(potential_salesteams_for_leads, lead_fit, salesteam['id'])
        print 'potential_salesteams_for_leads', potential_salesteams_for_leads

        # /!\ section_id contains a tuple
        dummyString = 'dummy'
        for lead_id, salesteams_ids in potential_salesteams_for_leads.iteritems():
            lead = [lead for lead in all_leads if lead['id'] == lead_id][0]
            print 'lead', lead
            while not lead['section_id'] and salesteams_ids:
                # electing a salesteam to get the lead
                r = randint(0, len(salesteams_ids) - 1)
                salesteam_id = salesteams_ids[r]
                salesteam = all_salesteams[salesteam_id]
                if salesteam['leads_count'] < salesteam['maximum_section_leads']:
                    # todo: write in db here
                    # updates value in all_leads and all_salesteams
                    lead['section_id'] = (salesteam['id'], dummyString)
                    salesteam['leads_count'] += 1
                else:
                    del salesteams_ids[r]
            print 'lead_after', lead






        # lead assignement to salesmen

        for _, salesteam in all_salesteams.iteritems():
            # domain = [('section_id', '=', salesteam['id'])]
            # todo: this [0] is not so nice, should I do otherwise ?
            team_leads = [lead for lead in all_leads if lead['section_id'] and lead['section_id'][0] == salesteam['id'] and not lead['user_id']]
            # need to decide which leads will be asigned, I first consider that's all of them
            to_assign_leads = team_leads
            # print 'to_assign_leads', to_assign_leads
            to_assign_leads_ids = [lead['id'] for lead in to_assign_leads]
            # print to_assign_leads_ids

            potential_salesmen_for_leads = {}
            for section_user in all_section_users:
                # print 'section_user'#, section_user
                # todo: this [0] is not so nice, should I do otherwise ?
                if section_user['section_id'][0] == salesteam['id']:
                    # get the filters of this salesman
                    section_user_domain = section_user['section_domain']
                    filter_ids = safe_eval(section_user_domain)[0][2]
                    filters = get_filters(filter_ids)
                    # print filters
                    # should be done otherwise, it represents a lot of accesses to the db
                    domain = [('id', 'in', to_assign_leads_ids)] + filters
                    lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
                    # print "lead_fit", lead_fit
                    if lead_fit:
                        list_to_dict_keys(potential_salesmen_for_leads, lead_fit, section_user)
            print 'dict', potential_salesmen_for_leads

            # leads in potential_salesmen_for_leads must be assigned how should if be done ?
            # write in the db the user_id, update the lead count on the users

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
