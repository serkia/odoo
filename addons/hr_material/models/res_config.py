
import urlparse
from openerp import fields, api, models

class HrConfigSettings(models.TransientModel):
    _inherit = 'hr.config.settings'

    @api.multi
    def get_default_alias_material(self):
        alias_name = False
        alias_id = self.env['ir.model.data'].xmlid_to_res_id('hr_material.mail_alias_material')
        if alias_id:
            alias_name = self.env['mail.alias'].browse(alias_id).alias_name
        return {'alias_prefix': alias_name}

    @api.multi
    def set_default_alias_material(self):
        for record in self:
            default_alias_prefix = record.get_default_alias_material()['alias_prefix']
            if record.alias_prefix != default_alias_prefix:
                alias_id = self.env['ir.model.data'].xmlid_to_res_id('hr_material.mail_alias_material')
                if alias_id:
                    self.env['mail.alias'].browse(alias_id).write({'alias_name': record.alias_prefix})
        return True

    @api.multi
    def get_default_alias_domain(self):
        alias_domain = self.env['ir.config_parameter'].get_param("mail.catchall.domain")
        if not alias_domain:
            domain = self.env["ir.config_parameter"].get_param("web.base.url")
            try:
                alias_domain = urlparse.urlsplit(domain).netloc.split(':')[0]
            except Exception:
                pass
        return {'alias_domain': alias_domain}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
