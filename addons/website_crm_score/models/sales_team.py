from openerp.osv import osv
from openerp import fields, api, models, SUPERUSER_ID
import datetime
from openerp.tools.safe_eval import safe_eval
from random import randint, uniform, choice
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

# todo: is this useful ?
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

    @api.one
    def _assigned_leads(self):
        self.assigned_leads = self.section_user_ids and sum(map(lambda x: x.leads_count, self.section_user_ids)) or 0

    @api.one
    def _capacity(self):
        self.capacity = self.section_user_ids and sum(map(lambda x: x.maximum_user_leads, self.section_user_ids)) or 0

    ratio = fields.Float(string='Ratio')
    section_domain = fields.Char('Domain')
    lead_ids = fields.One2many('crm.lead', 'section_id', string='Leads')
    leads_count = fields.Integer(compute='_count_leads')
    assigned_leads = fields.Integer(compute='_assigned_leads')
    # maximum_section_leads = fields.Integer('Maximum leads')
    capacity = fields.Integer(compute='_capacity')
    section_user_ids = fields.One2many('section.user', 'section_id', string='Salemen')

    def assign_leads(self, cr, uid, ids, context=None):

        def add_to_dict(d, k, v):
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]

        def list_to_dict_keys(d, l, v):
            for e in l:
                add_to_dict(d, e, v)
                # if e in d:
                #     d[e].append(v)
                # else:
                #     d[e] = [v]

        def weighted_random(d):
            s = sum([p for _, p in d.iteritems()])
            r = uniform(0, s)
            a = 0
            for e, p in d.iteritems():
                a += p
                if r < a:
                    return e
            # todo: should never happen -> maybe for approximation imprecision
            return choice([e for e, _ in d.iteritems()])

        """ Getting all the useful data from the db
        """
        salesteams_fields = ['section_domain',
                             'assigned_leads',
                             'capacity',
                             'name'
                             ]
        all_salesteams = self.search_read(cr, SUPERUSER_ID, fields=salesteams_fields, context=context)
        # casting the list into a dict to ease the access afterwards
        all_salesteams = {team['id']: team for team in all_salesteams}

        section_users_fields = ['section_user_domain',
                                'user_id',
                                'section_id',
                                'leads_count',
                                'maximum_user_leads',
                                'user_name',
                                'running',
                                'percentage_leads'
                                ]
        all_section_users = self.pool['section.user'].search_read(cr, SUPERUSER_ID, fields=section_users_fields, context=context)
        # adding the probability to bet a lead for each section user
        for section_user in all_section_users:
            try:
                section_user['probability'] = 1 - section_user['leads_count'] / float(section_user['maximum_user_leads'])
            except ZeroDivisionError:
                section_user['probability'] = 0
        # casting the list into a dict to ease the access afterwards
        all_section_users = {section_user['id']: section_user for section_user in all_section_users}

        # I would need all the fields of all leads... instead, there are some accesses to the db in the loops
        leads_fields = ['section_id',
                        'user_id',
                        'name',
                        'score'
                        ]
        all_leads = self.pool["crm.lead"].search_read(cr, SUPERUSER_ID, fields=leads_fields, context=context)
        # casting the list into a dict to ease the access afterwards
        all_leads = {lead['id']: lead for lead in all_leads}

        """ lead assignement to salesteams
        """
        potential_salesteams_for_leads = {}
        for _, salesteam in all_salesteams.iteritems():
            domain = salesteam['section_domain']
            if domain:
                domain = safe_eval(domain)
            else:
                domain = []
            # only addressing the lead that are unassigned
            domain.extend([('section_id', '=', False), ('user_id', '=', False)])
            lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
            if lead_fit:
                list_to_dict_keys(potential_salesteams_for_leads, lead_fit, salesteam['id'])

        # /!\ section_id contains a tuple, dummyString fills the tuple along with the id (same applies later for user_id)
        dummyString = 'dummy'
        for lead_id, salesteams_ids in potential_salesteams_for_leads.iteritems():
            lead = all_leads[lead_id]
            while not lead['section_id'] and salesteams_ids:
                # electing a salesteam to get the lead
                r = randint(0, len(salesteams_ids) - 1)
                salesteam_id = salesteams_ids[r]
                salesteam = all_salesteams[salesteam_id]
                self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead['id'], {'section_id': salesteam['id']}, context=context)
                # updates value in all_leads and all_salesteams
                lead['section_id'] = (salesteam['id'], dummyString)

        """ lead assignement to salesmen
        """
        for _, salesteam in all_salesteams.iteritems():

            """ Sorting the leads to assing depending on their score
                so that the leads with the best scores are assigned to salesmen first
                The sort is done once per salesteam
            """
            team_lead_ids = [lead['id'] for _, lead in all_leads.iteritems() if lead['section_id'] and lead['section_id'][0] == salesteam['id'] and not lead['user_id']]
            # map the leads to their score to sort when assigning
            scored_leads = {}
            for lead_id in team_lead_ids:
                add_to_dict(scored_leads, all_leads[lead_id]['score'], lead_id)
            # sort the keys of the dict so that the leads are assign first if they have a better score
            scores = sorted(scored_leads.keys(), reverse=True)
            # creating the actual lead order that will be used when assigning
            sorted_leads = []
            for score in scores:
                sorted_leads.extend(scored_leads[score])

            # Only considering as much leads as it is possible to assign
            capacity_left = salesteam['capacity'] - salesteam['assigned_leads']
            to_assign_leads_ids = sorted_leads[:capacity_left]

            potential_salesmen_for_leads = {}
            for _, section_user in all_section_users.iteritems():
                # todo: this [0] is not so nice, should I do otherwise ?
                if section_user['section_id'][0] == salesteam['id']:
                    # get the filters of this salesman
                    domain = section_user['section_user_domain']
                    if domain:
                        domain = safe_eval(domain)
                    else:
                        domain = []
                    domain.extend([('id', 'in', to_assign_leads_ids)])
                    # should be done otherwise, it represents a lot of accesses to the db
                    lead_fit = self.pool["crm.lead"].search(cr, SUPERUSER_ID, domain, context=context)
                    if lead_fit and section_user['running']:
                        list_to_dict_keys(potential_salesmen_for_leads, lead_fit, section_user['id'])

            # assign to leads to salesmen
            for lead_id in to_assign_leads_ids:
                section_user_ids = potential_salesmen_for_leads[lead_id]
                lead = all_leads[lead_id]
                while not lead['user_id'] and section_user_ids:
                    # electing a salesteam to get the lead and assigning it if match
                    proba_dict = {}
                    for section_user_id in section_user_ids:
                        section_user = all_section_users[section_user_id]
                        if section_user['probability']:
                            proba_dict[section_user_id] = section_user['probability']
                        else:
                            section_user_ids.remove(section_user_id)
                    if proba_dict:
                        section_user_id = weighted_random(proba_dict)
                        section_user = all_section_users[section_user_id]
                        data = {'user_id': section_user['user_id'][0], 'assign_date': fields.Datetime.now()}
                        self.pool["crm.lead"].write(cr, SUPERUSER_ID, lead['id'], data, context=context)
                        # updates value in all_leads and all_salesteams
                        lead['user_id'] = (section_user['user_id'], dummyString)
                        section_user['leads_count'] += 1
                        # recomputing the probability for the salesman that got the lead
                        # no need to check for ZeroDivisionError because if the section_user got a lead,
                        #   then it has a maximum_user_leads > 0
                        section_user['probability'] = 1 - section_user['leads_count'] / float(section_user['maximum_user_leads'])


class res_users(osv.Model):
    _inherit = 'res.users'

    @api.one
    def _count_leads(self):
        self.leads_count = self.lead_ids and sum(map(lambda x: 1, self.lead_ids)) or 0

    @api.one
    def _count_new_leads(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=7)
        self.new_leads_count = self.lead_ids and sum(map(lambda x: 1 if (now - fields.Datetime.from_string(x.create_date)) < delta else 0, self.lead_ids)) or 0

    lead_ids = fields.One2many('crm.lead', 'user_id', string='Leads')
    new_leads_count = fields.Integer(compute='_count_new_leads')
    leads_count = fields.Integer(compute='_count_leads')
    # running = fields.Boolean(string='Running', default=True)


class section_user(models.Model):
    _name = 'section.user'

    @api.one
    @api.model
    def _count_leads(self):
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        domain = [('user_id', '=', self.user_id.id),
                  ('section_id', '=', self.section_id.id),
                  ('assign_date', '>=', limit_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                  ]
        self.leads_count = self.env['crm.lead'].search_count(domain)

    @api.one
    def _get_percentage(self):
        try:
            self.percentage_leads = round(100 * self.leads_count / float(self.maximum_user_leads), 2)
        except ZeroDivisionError:
            self.percentage_leads = 0.0

    section_id = fields.Many2one('crm.case.section', string='SaleTeam', required=True)
    user_id = fields.Many2one('res.users', string='Saleman', required=True)
    user_name = fields.Char(related='user_id.partner_id.display_name')
    # running = fields.Boolean(related='user_id.running')
    running = fields.Boolean(string='Running', default=True)
    section_user_domain = fields.Char('Domain')
    maximum_user_leads = fields.Integer('Maximum leads')
    leads_count = fields.Integer(compute='_count_leads')
    percentage_leads = fields.Float(compute='_get_percentage', string='Percentage leads')

    @api.one
    def toggle_active(self):
        # todo: Can I do that or must I use a write ?
        self.running = not self.running
