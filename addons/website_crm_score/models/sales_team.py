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

        print 'Assigning leads'

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

        salesteams_fields = ['filter_ids', 'leads_count', 'maximum_section_leads', 'name']
        all_salesteams = self.search_read(cr, SUPERUSER_ID, fields=salesteams_fields, context=context)
        # casting the list into a dict to ease the access afterwards
        all_salesteams = {team['id']: team for team in all_salesteams}

        section_users_fields = ['section_domain', 'user_id', 'section_id', 'leads_count', 'maximum_user_leads', 'user_name', 'running']
        all_section_users = self.pool['section.user'].search_read(cr, SUPERUSER_ID, fields=section_users_fields, context=context)
        # casting the list into a dict to ease the access afterwards
        all_section_users = {section_user['id']: section_user for section_user in all_section_users}

        # I would need all the fields of all leads... instead, there are some accesses to the db in the loops
        leads_fields = ['section_id', 'user_id']
        all_leads = self.pool["crm.lead"].search_read(cr, SUPERUSER_ID, fields=leads_fields, context=context)
        # todo: creating a dict here might be a good idea to avoid the list comprehension to get one item

        # lead assignement to salesteams
        potential_salesteams_for_leads = {}
        for _, salesteam in all_salesteams.iteritems():
            filter_ids = salesteam['filter_ids']
            filters = get_filters(filter_ids)
            # should be done otherwise, it represents a lot of accesses to the db
            domain = [('section_id', '=', False), ('user_id', '=', False)] + filters
            lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
            if lead_fit:
                list_to_dict_keys(potential_salesteams_for_leads, lead_fit, salesteam['id'])
        # print 'potential_salesteams_for_leads', potential_salesteams_for_leads

        # /!\ section_id contains a tuple
        dummyString = 'dummy'
        for lead_id, salesteams_ids in potential_salesteams_for_leads.iteritems():
            lead = [lead for lead in all_leads if lead['id'] == lead_id][0]
            while not lead['section_id'] and salesteams_ids:
                # electing a salesteam to get the lead
                r = randint(0, len(salesteams_ids) - 1)
                salesteam_id = salesteams_ids[r]
                salesteam = all_salesteams[salesteam_id]
                if salesteam['leads_count'] < salesteam['maximum_section_leads']:
                    # todo: write in db here, to assign the lead to the team
                    # updates value in all_leads and all_salesteams
                    lead['section_id'] = (salesteam['id'], dummyString)
                    salesteam['leads_count'] += 1
                    print "Lead", lead['id'], "assigned to team", salesteam['id']
                    body = "Lead assigned to salesteam <b>" + salesteam['name'] + '</b>'
                    self.pool["crm.lead"].message_post(cr, SUPERUSER_ID, [lead['id']], body=body, subject="Auto-assign to salesteam", context=context)
                else:
                    del salesteams_ids[r]

        # lead assignement to salesmen
        for _, salesteam in all_salesteams.iteritems():
            # todo: this [0] is not so nice, should I do otherwise ?
            team_leads = [lead for lead in all_leads if lead['section_id'] and lead['section_id'][0] == salesteam['id'] and not lead['user_id']]
            # todo: need to decide which leads will be asigned, I first consider that's all of them
            to_assign_leads = team_leads
            to_assign_leads_ids = [lead['id'] for lead in to_assign_leads]

            potential_salesmen_for_leads = {}
            for _, section_user in all_section_users.iteritems():
                # todo: this [0] is not so nice, should I do otherwise ?
                if section_user['section_id'][0] == salesteam['id']:
                    # get the filters of this salesman
                    section_user_domain = section_user['section_domain']
                    filter_ids = safe_eval(section_user_domain)[0][2]
                    filters = get_filters(filter_ids)
                    # should be done otherwise, it represents a lot of accesses to the db
                    domain = [('id', 'in', to_assign_leads_ids)] + filters
                    lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
                    if lead_fit and section_user['running']:
                        list_to_dict_keys(potential_salesmen_for_leads, lead_fit, section_user['id'])
            # print 'dict', potential_salesmen_for_leads

            # assign to leads to salesmen
            for lead_id, section_user_ids in potential_salesmen_for_leads.iteritems():
                lead = [lead for lead in all_leads if lead['id'] == lead_id][0]
                while not lead['user_id'] and section_user_ids:
                    # electing a salesteam to get the lead
                    r = randint(0, len(section_user_ids) - 1)
                    section_user_id = section_user_ids[r]
                    section_user = all_section_users[section_user_id]
                    if section_user['leads_count'] < section_user['maximum_user_leads']:
                        # todo: write in the db, to assign lead to salesmen
                        # updates value in all_leads and all_salesteams
                        lead['user_id'] = (section_user['user_id'], dummyString)
                        section_user['leads_count'] += 1
                        body = "Lead assigned to salesman <b>" + section_user['user_name'] + '</b>'
                        self.pool["crm.lead"].message_post(cr, SUPERUSER_ID, [lead['id']], body=body, subject="Auto-assign to salesman", context=context)
                        print "Lead", lead['id'], "assigned to user", section_user['user_id']
                    else:
                        del section_user_ids[r]

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

    lead_ids = fields.One2many('crm.lead', 'user_id', string='Leads')
    new_leads_count = fields.Integer(compute='_count_new_leads')
    leads_count = fields.Integer(compute='_count_leads')
    running = fields.Boolean(string='Running', default=True)


class section_user(models.Model):
    _name = 'section.user'

    @api.one
    @api.model
    def _count_leads(self):
        domain = [('user_id', '=', self.user_id.id), ('section_id', '=', self.section_id.id)]
        self.leads_count = self.env['crm.lead'].search_count(domain)

    @api.one
    def _get_percentage(self):
        try:
            self.percentage_leads = 100 * self.user_id.leads_count / float(self.maximum_user_leads)
        except ZeroDivisionError:
            self.percentage_leads = 0.0

    section_id = fields.Many2one('crm.case.section', string='SaleTeam', required=True)
    user_id = fields.Many2one('res.users', string='Saleman', required=True)
    user_name = fields.Char(related='user_id.partner_id.display_name')
    running = fields.Boolean(related='user_id.running')
    section_domain = fields.Char('Domain')
    maximum_user_leads = fields.Integer('Maximum leads')
    leads_count = fields.Integer(compute='_count_leads')
    percentage_leads = fields.Float(compute='_get_percentage', string='Percentage leads')

    @api.one
    def toggle_active(self):
        if self.running:
            # todo: Can I do that or must I use a write ?
            self.running = False
        else:
            # todo: Same question
            self.running = True
