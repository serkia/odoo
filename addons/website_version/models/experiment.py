# -*- coding: utf-8 -*-
from openerp.osv import osv, fields

class Experiment_snapshot(osv.Model):
    _name = "website_version.experiment_snapshot"
    
    _columns = {
        'snapshot_id': fields.many2one('website_version.snapshot',string="Snapshot_id",required=True ,ondelete='cascade'),
        'experiment_id': fields.many2one('website_version.experiment',string="Experiment_id",required=True),
        'frequency': fields.selection([('10','Rare'),('50','Sometimes'),('100','Offen')], 'Frequency'),
    }

    _defaults = {
        'frequency': '10',
    }


class Experiment(osv.Model):
    _name = "website_version.experiment"
    _inherit = ['mail.thread']

    STATES = [('draft','Draft'),('running','Running'),('done','Done')]

    def _get_version_number(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for exp in self.browse(cr, uid, ids, context=context):
            result[exp.id] = 0
            sum_pond = 0
            for exp_snap in exp.experiment_snapshot_ids:
                    sum_pond += int(exp_snap.frequency)
                    result[exp.id] += 1
            if sum_pond < 100:
                #We must considerate master
                result[exp.id] += 1
        return result

    # def _get_state(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
    #     from pudb import set_trace; set_trace()
    #     return STATES, {}
    
    _columns = {
        'name': fields.char(string="Title", size=256, required=True),
        'experiment_snapshot_ids': fields.one2many('website_version.experiment_snapshot', 'experiment_id',string="experiment_snapshot_ids"),
        'website_id': fields.many2one('website',string="Website", required=True),
        'state': fields.selection(STATES, 'Status', required=True, copy=False, track_visibility='onchange'),
        'color': fields.integer('Color Index'),
        'version_number' : fields.function(_get_version_number,type='integer'),
        'sequence': fields.integer('Sequence', required=True, help="Test."),
    }

    _defaults = {
        'state': 'draft',
        'sequence': 1,
    }

    _order = 'sequence'

    _group_by_full = {
        # 'state': _get_state
        'state': lambda *args, **kwargs : ([('draft','Draft'),('running','Running'),('done','Done')], dict()),
    }

