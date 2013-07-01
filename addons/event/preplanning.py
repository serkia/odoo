# -*- coding: utf-8 ⁻*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2013-TODAY OpenERP S.A. (<http://openerp.com>).
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

from datetime import datetime
from dateutil.relativedelta import relativedelta, MO
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FMT


class EventPreplanning(osv.TransientModel):
    _name = 'event.event.preplanning'

    def name_get(self, cr, uid, ids, context=None):
        return [(x['id'], _('Preplanning: %s') % x['name'])
                for x in self.read(cr, uid, ids, ['name'], context=context)]

    def _get_children_ids(self,  cr, uid, ids, fieldname, args, context=None):
        result = {}
        for preplan in self.browse(cr, uid, ids, context=context):
            result[preplan.id] = [child.id for child in preplan.event_id.seance_ids]
        return result

    def _set_children_ids(self, cr, uid, id, fieldname, values, args, context=None):
        result = []
        if not values:
            return result
        from pprint import pprint
        Seance = self.pool.get('event.seance')
        for val in values:
            if val[0] == 0:
                pprint(val[2])
                id_new = Seance.create(cr, uid, val[2], context=context)
                result += Seance._store_get_values(cr, uid, [id_new], val[2].keys(), context)
            elif val[0] == 2:
                Seance.unlink(cr, uid, [val[1]], context=context)
            elif val[0] == 4:
                pass  # event should already be attached to this offer (preplanning)
        return result

    _columns = {
        'event_id': fields.many2one('event.event', 'Event Id'),
        'name': fields.related('event_id', 'name', type='char', string='Name', readonly=True),
        'date_begin': fields.related('event_id', 'date_begin', type='datetime', string='Begin date', readonly=True),
        'date_end': fields.datetime('End date', required=True),
        # 'children_ids': fields.related('event_id', 'children_ids', type='one2many', relation='event.event', readonly=True),
        'children_ids': fields.function(_get_children_ids, type='one2many', relation='event.seance',
                                        fnct_inv=_set_children_ids, string='Children Events'),
    }

    def create(self, cr, uid, values, context=None):
        if values and values.get('event_id') and not values.get('date_end'):
            event_obj = self.pool.get('event.event')
            current_end_date = event_obj.browse(cr, uid, values['event_id'], context=context).date_end
            # TODO: compute 'estimated end date' and take max of (current_date_date, estimated_date_end) + next monday
            values['date_end'] = current_end_date
        return super(EventPreplanning, self).create(cr, uid, values, context=context)

    def get_info(self, cr, uid, event_id, date_begin, date_end, context=None):
        if context is None:
            context = {}
        if not event_id:
            return {}
        result = {'contents': [], 'weeks': []}
        event = self.pool.get('event.event').browse(cr, uid, event_id, context=context)
        week_start_day = MO

        estimated_date_end = event.date_end  # TODO: need to compute estimated end date using get_estimated_end_date()
        date_begin = datetime.strptime(max(event.date_begin, date_begin), DT_FMT) + relativedelta(weekday=week_start_day(-1))
        date_begin = date_begin.replace(hour=0, minute=0, second=0)
        date_end = datetime.strptime(max(event.date_end, estimated_date_end), DT_FMT) + relativedelta(weekday=week_start_day(+1))
        date_end = date_end.replace(hour=23, minute=59, second=59)

        lang_name = context.get('lang') or self.pool.get('res.users').context_get(cr, uid, uid)['lang']
        lang_ids = self.pool.get('res.lang').search(cr, uid, [('code', '=', lang_name)], limit=1, context=context)
        lang = self.pool.get('res.lang').browse(cr, uid, lang_ids[0], context=context)

        result['defaults'] = dict(
            tz=event.tz,
            # calendar_id=event.calendar_id.id,
            # registration_ok=False # TODO: allow open/close registration
        )

        for content in event.content_ids:
            result['contents'].append({
                'id': content.id,
                'name': content.name,
                'type_id': content.type_id.id or False,
                'course_id': content.course_id.id or False,
                'groups': [g.id for g in content.group_ids],
                'slot_count': content.slot_count,
                'slot_used': 0,
                'slot_duration': content.slot_duration,
            })

        wd = date_begin.replace()
        while wd <= date_end:
            wd_end = wd + relativedelta(weeks=1)
            result['weeks'].append({
                'id': wd.strftime('%Y%V'),  # ISO YEAR + ISO WEEK NUMBER
                'name': wd.strftime(lang.date_format),
                'start': wd.strftime(DT_FMT),
                'stop': wd_end.strftime(DT_FMT),
                'slot_count': 10,  # TODO: compute this using real calendar + unavailibility informations
                'slot_used': 0,
            })
            wd = wd_end
        return result