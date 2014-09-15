import openerp
from openerp import http
from openerp.http import request
import datetime

class TableExporter(http.Controller):
        
    @http.route(['/website_version/change_snapshot'], type = 'json', auth = "user", website = True)
    def change_snapshot(self, snapshot_id):
        request.session['snapshot_id'] = int(snapshot_id)
        request.session['master'] = 0
        return snapshot_id

    @http.route(['/website_version/master'], type = 'json', auth = "user", website = True)
    def master(self):
        request.session['snapshot_id'] = 0
        request.session['master'] = 1
        return 0

    @http.route(['/website_version/create_snapshot'], type = 'json', auth = "user", website = True)
    def create_snapshot(self,name):
        cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
        if name == "":
            name = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        snapshot_id = context.get('snapshot_id')
        iuv = request.registry['ir.ui.view']
        snap = request.registry['website_version.snapshot']
        website_id = request.website.id
        if not snapshot_id:
            new_snapshot_id = snap.create(cr, uid,{'name':name, 'website_id':website_id}, context=context)
        else:
            new_snapshot_id = snap.create(cr, uid,{'name':name, 'website_id':website_id}, context=context)
            iuv.copy_snapshot(cr, uid, snapshot_id,new_snapshot_id,context=context)
        request.session['snapshot_id'] = new_snapshot_id
        request.context['snapshot_id'] = new_snapshot_id
        request.session['master'] = 0
        return name

    @http.route(['/website_version/delete_snapshot'], type = 'json', auth = "user", website = True)
    def delete_snapshot(self, snapshot_id):
        cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
        snap = request.registry['website_version.snapshot']
        snap.unlink(cr, uid, [int(snapshot_id)], context=context)
        request.session['snapshot_id'] = 0
        request.session['master'] = 1
        return snapshot_id
    
    @http.route(['/website_version/all_snapshots'], type = 'json', auth = "public", website = True)
    def get_all_snapshots(self):
        cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
        snap = request.registry['website_version.snapshot']
        website_id = request.website.id
        ids = snap.search(cr, uid, [('website_id','=',website_id)],context=context)
        result = snap.read(cr, uid, ids,['id','name'],context=context)
        return result

    @http.route(['/website_version/is_master'], type = 'json', auth = "public", website = True)
    def is_master(self, view_id):
        cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
        obj = request.registry['ir.ui.view']
        view = obj.browse(cr,uid,[int(view_id)],context=context)
        if view.snapshot_id:
            result = False
        else:
            result = True
        return result

    @http.route(['/set_context'], type = 'json', auth = "public", website = True)
    def set_context(self):
        cr, uid, context = request.cr, openerp.SUPERUSER_ID, request.context
        snapshot_id = context.get('snapshot_id')
        return snapshot_id
