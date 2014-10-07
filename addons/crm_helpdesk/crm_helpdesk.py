# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp
from openerp.addons.crm import crm
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.tools import html2plaintext

class crm_helpdesk_stage(osv.osv):
    """ Model for helpdesk stages. This models the main stages of a helpdesk
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "crm.helpdesk.stage"
    _description = "helpdesk stages"
    _rec_name = 'name'
    _order = "sequence"

    _columns = {
        'name': fields.char('Stage Name', required=True, translate=True),
        'sequence': fields.integer('Sequence', help="Used to order stages. Lower is better."),
        'section_ids':fields.many2many('crm.case.section', 'section_helpdesk_stage_rel', 'stage_id', 'section_id', string='Sections',
                        help="Link between stages and sales teams. When set, this limitate the current stage to the selected sales teams."),
        'case_default': fields.boolean('Common to All Teams',
                        help="If you check this field, this stage will be proposed by default on each sales team. It will not assign this stage to existing teams."),
        'fold': fields.boolean('Folded in Kanban View',
                               help='This stage is folded in the kanban view when'
                               'there are no records in that stage to display.')
    }

    _defaults = {
        'sequence': lambda *args: 1,
    }

class crm_helpdesk(osv.osv):
    """ Helpdesk Cases """

    _name = "crm.helpdesk"
    _description = "Helpdesk"
    _order = "priority, id desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _mail_post_access = 'read'
    _track = {
        'stage_id': {
            # this is only an heuristics; depending on your particular stage configuration it may not match all 'new' stages
            'crm_helpdesk.mt_helpdesk_new': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence <= 1,
            'crm_helpdesk.mt_helpdesk_stage': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence > 1,
        },
        'user_id': {
            'crm_helpdesk.mt_helpdesk_assigned': lambda self, cr, uid, obj, ctx=None: obj.user_id and obj.user_id.id,
        },
        'kanban_state': {
            'crm_helpdesk.mt_helpdesk_blocked': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'blocked',
            'crm_helpdesk.mt_helpdesk_ready': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'done',
        },
    }
    def _get_default_partner(self, cr, uid, context=None):
        section_id = self._get_default_section_id(cr, uid, context)
        if section_id:
            section = self.pool.get('crm.lead').browse(cr, uid, section_id, context=context)
            if section and section.partner_id:
                return section.partner_id.id
        return False

    def _get_default_section_id(self, cr, uid, context=None):
        """ Gives default section by checking if present in the context """
        return self.pool.get('crm.lead')._resolve_section_id_from_context(cr, uid, context=context) or False

    def _get_default_stage_id(self, cr, uid, context=None):
        """ Gives default stage_id """
        section_id = self._get_default_section_id(cr, uid, context=context)
        return self.stage_find(cr, uid, [], section_id, [('sequence', '=', '1')], context=context)

    def _resolve_section_id_from_context(self, cr, uid, context=None):
        """ Returns ID of claim based on the value of 'default_section_id'
            context key, or None if it cannot be resolved to a single
            section.
        """
        if context is None:
            context = {}
        if type(context.get('default_section_id')) in (int, long):
            return context.get('default_section_id')
        if isinstance(context.get('default_section_id'), basestring):
            section_name = context['default_section_id']
            section_ids = self.pool.get('crm.lead').name_search(cr, uid, name=section_name, context=context)
            if len(section_ids) == 1:
                return int(section_ids[0][0])
        return None

    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        access_rights_uid = access_rights_uid or uid
        stage_obj = self.pool.get('crm.helpdesk.stage')
        order = stage_obj._order
        # lame hack to allow reverting search, should just work in the trivial case
        if read_group_order == 'stage_id desc':
            order = "%s desc" % order
        # retrieve section_id from the context and write the domain
        # - ('id', 'in', 'ids'): add columns that should be present
        # - OR ('case_default', '=', True), ('fold', '=', False): add default columns that are not folded
        # - OR ('section_ids', 'in', section_id), ('fold', '=', False) if section_id: add section columns that are not folded
        search_domain = []
        section_id = self._resolve_section_id_from_context(cr, uid, context=context)
        if section_id:
            search_domain += ['|', ('section_ids', '=', section_id)]
        search_domain += [('id', 'in', ids)]
        # perform search
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x,y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold

    _columns = {
            'id': fields.integer('ID', readonly=True),
            'name': fields.char('Name', required=True),
            'active': fields.boolean('Active', required=False),
            'date_action_last': fields.datetime('Last Action', readonly=1),
            'date_action_next': fields.datetime('Next Action', readonly=1),
            'description': fields.text('Description'),
            'create_date': fields.datetime('Creation Date' , readonly=True),
            'write_date': fields.datetime('Update Date' , readonly=True),
            'date_deadline': fields.date('Deadline'),
            'user_id': fields.many2one('res.users', 'Responsible', track_visibility='always'),
            'section_id': fields.many2one('crm.case.section', 'Sales Team', \
                            select=True, help='Responsible sales team. Define Responsible user and Email account for mail gateway.'),
            'company_id': fields.many2one('res.company', 'Company'),
            'date_closed': fields.datetime('Closed', readonly=True),
            'partner_id': fields.many2one('res.partner', 'Partner'),
            'email_cc': fields.text('Watchers Emails', size=252 , help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma"),
            'email_from': fields.char('Email', size=128, help="Destination email for email gateway"),
            'date': fields.datetime('Date'),
            'date_last_stage_update': fields.datetime('Last Stage Update', select=True),
            'ref': fields.reference('Reference', selection=openerp.addons.base.res.res_request.referencable_models),
            'ref2': fields.reference('Reference 2', selection=openerp.addons.base.res.res_request.referencable_models),
            'channel_id': fields.many2one('crm.tracking.medium', 'Channel', help="Communication channel."),
            'planned_revenue': fields.float('Planned Revenue'),
            'planned_cost': fields.float('Planned Costs'),
            'priority': fields.selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority'),
            'probability': fields.float('Probability (%)'),
            'categ_id': fields.many2one('crm.case.categ', 'Tags', \
                            domain="['|',('section_id','=',False),('section_id','=',section_id),\
                            ('object_id.model', '=', 'crm.helpdesk')]"),
            'duration': fields.float('Duration', states={'done': [('readonly', True)]}),
            'color': fields.integer('Color Index'),
            'stage_id': fields.many2one ('crm.helpdesk.stage', 'Stage', track_visibility='onchange',
                domain="['|', ('section_ids', '=', section_id), ('case_default', '=', True)]"),
            'kanban_state': fields.selection([('normal', 'Normal'),('blocked', 'Blocked'),('done', 'Ready for next stage')], 'Kanban State',
                                         track_visibility='onchange',
                                         help="A helpdesk's kanban state indicates special situations affecting it:\n"
                                              " * Normal is the default situation\n"
                                              " * Blocked indicates something is preventing the progress of this issue\n"
                                              " * Ready for next stage indicates the helpdesk is ready to be pulled to the next stage",
                                         required=False),
    }

    _defaults = {
        'active': lambda *a: 1,
        'user_id': lambda s, cr, uid, c: uid,
        'kanban_state': 'normal',
        'section_id': lambda s, cr, uid, c: s._get_default_section_id(cr, uid, c),
        'date_last_stage_update': fields.datetime.now,
        'stage_id': lambda s, cr, uid, c: s._get_default_stage_id(cr, uid, c),
        'date': fields.datetime.now,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.case', context=c),
        'priority': '1',
    }

    _group_by_full = {
        'stage_id': _read_group_stage_ids
    }

    def stage_find(self, cr, uid, cases, section_id, domain=[], order='sequence', context=None):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default case
        """
        if isinstance(cases, (int, long)):
            cases = self.browse(cr, uid, cases, context=context)
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        for helpdesk in cases:
            if helpdesk.section_id:
                section_ids.append(helpdesk.section_id.id)
        # OR all section_ids and OR with case_default
        search_domain = []
        if section_ids:
            search_domain += [('|')] * len(section_ids)
            for section_id in section_ids:
                search_domain.append(('section_ids', '=', section_id))
        search_domain.append(('case_default', '=', True))
        # AND with the domain in parameter
        search_domain += list(domain)
        # perform search, return the first found
        stage_ids = self.pool.get('crm.helpdesk.stage').search(cr, uid, search_domain, order=order, context=context)
        if stage_ids:
            return stage_ids[0]
        return False

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        values = {}
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            values = {
                'email_from': partner.email,
            }
        return {'value': values}

    def create(self, cr, uid, vals, context=None):
        context = dict(context or {})
        if vals.get('section_id') and not context.get('default_section_id'):
            context['default_section_id'] = vals.get('section_id')

        # context: no_log, because subtype already handle this
        create_context = dict(context, mail_create_nolog=True)
        return super(crm_helpdesk, self).create(cr, uid, vals, context=create_context)

    def copy(self, cr, uid, id, default=None, context=None):
        helpdesk = self.browse(cr, uid, id, context=context)
        default = dict(default or {},
            stage_id = self._get_default_stage_id(cr, uid, context=context),
            name = _('%s (copy)') % helpdesk.name)
        return super(crm_helpdesk, self).copy(cr, uid, id, default, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            vals['date_last_stage_update'] = fields.datetime.now()
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
        # user_id change: update date_start
        if vals.get('user_id'):
            vals['date_start'] = fields.datetime.now()
        return super(crm_helpdesk, self).write(cr, uid, ids, vals, context)

    def case_escalate(self, cr, uid, ids, context=None):
        """ Escalates case to parent level """
        data = {'active': True}
        for case in self.browse(cr, uid, ids, context=context):
            if case.section_id and case.section_id.parent_id:
                parent_id = case.section_id.parent_id
                data['section_id'] = parent_id.id
                if parent_id.change_responsible and parent_id.user_id:
                    data['user_id'] = parent_id.user_id.id
            else:
                raise osv.except_osv(_('Error!'), _('You can not escalate, you are already at the top level regarding your sales-team category.'))
            self.write(cr, uid, [case.id], data, context=context)
        return True

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------

    def message_get_reply_to(self, cr, uid, ids, context=None):
        """ Override to get the reply_to of the parent project. """
        helpdesks = self.browse(cr, SUPERUSER_ID, ids, context=context)
        section_ids = set([helpdesk.section_id.id for helpdesk in helpdesks if helpdesk.section_id])
        aliases = self.pool['crm_helpdesk'].message_get_reply_to(cr, uid, list(section_ids), context=context)
        return dict((helpdesk.id, aliases.get(helpdesk.section_id and helpdesk.section_id.id or 0, False)) for helpdesk in helpdesks)

    def message_get_suggested_recipients(self, cr, uid, ids, context=None):
        recipients = super(crm_helpdesk, self).message_get_suggested_recipients(cr, uid, ids, context=context)
        try:
            for helpdesk in self.browse(cr, uid, ids, context=context):
                if helpdesk.partner_id:
                    self._message_add_suggested_recipient(cr, uid, recipients, helpdesk, partner=helpdesk.partner_id, reason=_('Customer'))
                elif helpdesk.email_from:
                    self._message_add_suggested_recipient(cr, uid, recipients, helpdesk, email=helpdesk.email_from, reason=_('Customer Email'))
        except (osv.except_osv, orm.except_orm):  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
        }
        defaults.update(custom_values)
        return super(crm_helpdesk, self).message_new(cr, uid, msg, custom_values=defaults, context=context)

    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification', subtype=None, parent_id=False, attachments=None, context=None, content_subtype='html', **kwargs):
        """ Overrides mail_thread message_post so that we can set the date of last action field when
            a new message is posted on the issue.
        """
        if context is None:
            context = {}
        res = super(crm_helpdesk, self).message_post(cr, uid, thread_id, body=body, subject=subject, type=type, subtype=subtype, parent_id=parent_id, attachments=attachments, context=context, content_subtype=content_subtype, **kwargs)
        if thread_id and subtype:
            self.write(cr, SUPERUSER_ID, thread_id, {'date_action_next': fields.datetime.now()}, context=context)
        return res

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _helpdesk_count(self, cr, uid, ids, field_name, arg, context=None):
        Helpdesk = self.pool['crm.helpdesk']
        return {
            partner_id: Helpdesk.search_count(cr,uid, [('partner_id', '=', partner_id)], context=context)
        for partner_id in ids
    }

    _columns = {
    'helpdesk_count': fields.function(_helpdesk_count, string='# Helpdesk', type='integer'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
