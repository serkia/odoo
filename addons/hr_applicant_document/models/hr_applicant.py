# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class hr_applicant(osv.Model):
    _inherit = 'hr.applicant'

    def _get_attachments(self, cr, uid, ids, fields, args, context=None):
        res = dict.fromkeys(ids, '')
        Attachment = self.pool.get('ir.attachment')
        attachment_ids = Attachment.search(cr, uid, [('res_model', '=', 'hr.applicant'), ('res_id', 'in', ids)], context=context)
        res[attachment_ids] = attachment_ids
        return res

    def _content_search(self, cr, user, obj, name, args, context=None):
        record_ids = set()
        Attachment = self.pool.get('ir.attachment')
        args = ['&'] + args + [('res_model', '=', 'hr.applicant')]
        att_ids = Attachment.search(cr, user, args, context=context)
        record_ids = set(att.res_id for att in Attachment.browse(cr, user, att_ids, context=context))
        return [('id', 'in', list(record_ids))]

    _columns = {
        'attachment_ids': fields.function(_get_attachments, relation='ir.attachment',
            string='Resume Content', fnct_search=_content_search, type='one2many'),
    }
