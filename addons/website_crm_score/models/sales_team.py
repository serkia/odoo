from openerp.osv import osv
from openerp import fields, api, models
import datetime
from openerp.tools.safe_eval import safe_eval
from random import randint, uniform, choice
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class crm_case_section(osv.osv):
    _inherit = "crm.case.section"

    @api.one
    def _count_leads(self):
        self.leads_count = len(self.lead_ids)

    @api.one
    def _assigned_leads(self):
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        domain = [('assign_date', '>=', limit_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                  ('section_id', '=', self.id),
                  ('user_id', '!=', False)
                  ]
        self.assigned_leads = self.env['crm.lead'].search_count(domain)

    @api.one
    def _unassigned_leads(self):
        self.unassigned_leads = self.env['crm.lead'].search_count([('section_id', '=', self.id), ('user_id', '=', False)])

    @api.one
    def _capacity(self):
        self.capacity = sum(s.maximum_user_leads for s in self.section_user_ids) or 0

    ratio = fields.Float(string='Ratio')
    score_section_domain = fields.Char('Domain')
    lead_ids = fields.One2many('crm.lead', 'section_id', string='Leads')
    leads_count = fields.Integer(compute='_count_leads')
    assigned_leads = fields.Integer(compute='_assigned_leads')
    unassigned_leads = fields.Integer(compute='_unassigned_leads')
    capacity = fields.Integer(compute='_capacity')
    section_user_ids = fields.One2many('section.user', 'section_id', string='Salemen')

    @api.model
    def assign_leads(self, ids=[]):
        # note: this is old api translated to new api
        # benefit could be taken from records I guess
        # and do write operations require a browse right before ?

        def add_to_dict(d, k, v):
            if k in d:
                d[k].append(v)
            else:
                d[k] = [v]

        def list_to_dict_keys(d, l, v):
            for e in l:
                add_to_dict(d, e, v)

        def weighted_random(d):
            s = sum([p for _, p in d.iteritems()])
            r = uniform(0, s)
            a = 0
            for e, p in d.iteritems():
                a += p
                if r < a:
                    return e
            # should never happen -> maybe for approximation imprecision
            return choice([e for e, _ in d.iteritems()])

        def remove_spam_leads():

            def unary_domain(d):
                # this function takes a domain d and return the unary equivalent
                # eg: let any 3-tuple ('criteria', 'op', 'value') be written as d# (d1, d2, d3...)
                #   - unary :
                #           - [d1]            = d1
                #           - ['!', d1]       = -d1
                #           - ['|', d1, d2]   = d1 | d2
                #           - ['&', d1, d2]   = d1 & d2
                #           - ['|', '!', d1, '&', d2, d3] = -d1 | (d2 & d3)
                #   - not unary :
                #           - [d1, d2]  = d1 & d2 ('&' is not explicit)
                #               in the latter case, there are 2 unary expressions
                #           - ['!', d1, d2, d3] = -d1 & d2 & d3 ('&' are not explicit)
                #               in the latter case, there are 3 unary expressions
                #
                # the following loop count the number of unary expression in d and adds as many (minus one) '&' at the begining of the domain
                #   - d# counts as one unary expression
                #   - '!' doesn't count as a unary expression (['!', d1] = -d1)
                #   - '|' and '&' count as minus one unary expression because it is a binary operation (['|', d1, d2] = d1 | d2)
                #

                n = 0
                for e in d:
                    if e == '!':
                        pass
                    elif e == '|' or e == '&':
                        n -= 1
                    else:  # e is a 3-tuple (maybe the type should be checked)
                        n += 1
                u = ['&'] * (n - 1) + d
                return u

            # FIXME: if a filter is not well written, it causes a problem
            action = self.env['ir.actions.actions'].search([('name', '=', 'SpamIrFilter')])
            domain = [('action_id', '=', action.id)]
            all_spam_filters = self.env['ir.filters'].search_read(domain, fields=['domain'])

            all_domain = []
            nb_filters = 0

            # computing one domain for all the spam filters
            # disjunction of the unary domains
            for spam_filter in all_spam_filters:
                # NODE: as many db access as there are filters... (might be huge)
                u_domain = unary_domain(safe_eval(spam_filter['domain']))
                if u_domain:
                    all_domain.extend(u_domain)
                    nb_filters += 1
            all_domain = ['|'] * (nb_filters - 1) + all_domain
            # print 'all_domain', all_domain

            # searching for all leads matching spam filters
            spam_leads = self.env["crm.lead"].search(all_domain)
            for spam_lead in spam_leads:
                # print 'spam_lead', spam_lead
                pass

        def assign_leads_to_salesteams(all_salesteams, all_leads):
            # lead assignement to salesteams
            potential_salesteams_for_leads = {}
            for _, salesteam in all_salesteams.iteritems():
                domain = salesteam['score_section_domain']
                if domain:
                    domain = safe_eval(domain)
                else:
                    domain = []
                # only addressing the lead that are unassigned
                domain.extend([('section_id', '=', False), ('user_id', '=', False)])
                lead_fit = self.env["crm.lead"].search(domain)
                if lead_fit:
                    lead_fit = [lead.id for lead in lead_fit]
                    list_to_dict_keys(potential_salesteams_for_leads, lead_fit, salesteam['id'])

            # /!\ section_id contains a tuple, dummyString fills the tuple along with the id (same applies later for user_id)
            for lead_id, salesteams_ids in potential_salesteams_for_leads.iteritems():
                lead = all_leads[lead_id]
                while not lead['section_id'] and salesteams_ids:
                    # electing a salesteam to get the lead
                    r = randint(0, len(salesteams_ids) - 1)
                    salesteam_id = salesteams_ids[r]
                    salesteam = all_salesteams[salesteam_id]
                    lead_record = self.env['crm.lead'].browse(lead['id'])
                    # NOTE: the write takes 0.04 seconds, which is huge
                    lead_record.write({'section_id': salesteam['id']})
                    # updates value in all_leads and all_salesteams
                    lead['section_id'] = (salesteam['id'], '')

        def assign_leads_to_salesmen(self, all_salesteams, all_leads, all_section_users):
            # lead assignement to salesmen
            for _, salesteam in all_salesteams.iteritems():
                # Sorting the leads to assing depending on their score
                # so that the leads with the best scores are assigned to salesmen first
                # The sort is done once per salesteam

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
                # This is not enough because if one of the leads in to_assign_leads_ids
                #   cannot be assigned, then the capacity_left +1 must be considered
                # capacity_left = salesteam['capacity'] - salesteam['assigned_leads']
                # to_assign_leads_ids = sorted_leads[:capacity_left]

                potential_salesmen_for_leads = {}
                for _, section_user in all_section_users.iteritems():
                    if section_user['section_id'][0] == salesteam['id'] and section_user['running']:
                        # get the filters of this salesman
                        domain = section_user['section_user_domain']
                        if domain:
                            domain = safe_eval(domain)
                        else:
                            domain = []
                        # domain.extend([('id', 'in', to_assign_leads_ids)])
                        domain.extend([('id', 'in', sorted_leads)])
                        # should be done otherwise, it represents a lot of accesses to the db
                        lead_fit = self.env["crm.lead"].search(domain)
                        if lead_fit:
                            lead_fit = [lead.id for lead in lead_fit]
                            list_to_dict_keys(potential_salesmen_for_leads, lead_fit, section_user['id'])

                assignable_leads = potential_salesmen_for_leads.keys()
                # assign to leads to salesmen
                for lead_id in sorted_leads:
                    # the following condition is necessary in the case of a lead having no potential_salesman
                    if lead_id in assignable_leads:
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

                                lead_record = self.env['crm.lead'].browse(lead['id'])
                                lead_record.write(data)

                                # updates value in all_leads and all_salesteams
                                lead['user_id'] = (section_user['user_id'], '')
                                section_user['leads_count'] += 1
                                # recomputing the probability for the salesman that got the lead
                                # no need to check for ZeroDivisionError because if the section_user got a lead,
                                #   then it has a maximum_user_leads > 0
                                section_user['probability'] = 1 - section_user['leads_count'] / float(section_user['maximum_user_leads'])

        #
        # Getting all the useful data from the db
        #
        salesteams_fields = ['score_section_domain',
                             'assigned_leads',
                             'capacity',
                             'name'
                             ]
        all_salesteams = self.search_read(fields=salesteams_fields)
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
        all_section_users = self.env['section.user'].search_read(fields=section_users_fields)
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
        all_leads = self.env["crm.lead"].search_read(fields=leads_fields)
        # casting the list into a dict to ease the access afterwards
        all_leads = {lead['id']: lead for lead in all_leads}
        remove_spam_leads()  # match the filters that allow to filter spam leads

        #
        # Assigning the leads to salesteams and salesmen
        #
        assign_leads_to_salesteams(all_salesteams, all_leads)
        assign_leads_to_salesmen(self, all_salesteams, all_leads, all_section_users)


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


class section_user(models.Model):
    _name = 'section.user'

    @api.one
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
    running = fields.Boolean(string='Running', default=True)
    section_user_domain = fields.Char('Domain')
    maximum_user_leads = fields.Integer('Maximum leads')
    leads_count = fields.Integer(compute='_count_leads')
    percentage_leads = fields.Float(compute='_get_percentage', string='Percentage leads')

    @api.one
    def toggle_active(self):
        self.running = not self.running
