from openerp.osv import osv
from openerp import fields


class view(osv.osv):
    _inherit = "ir.ui.view"

    track = fields.Boolean(string='Track', default=False)
