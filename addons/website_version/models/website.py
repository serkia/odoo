# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp.http import request


class NewWebsite(osv.Model):
    _inherit = "website"

    _columns = {
        'snapshot_id':fields.many2one("website_version.snapshot",string="Snapshot"),
    }

    def get_current_snapshot(self,cr,uid,context=None):
        id=request.session.get('snapshot_id')
        ob=self.pool['website_version.snapshot'].browse(cr,uid,[id],context=context)
        return ob[0].name
