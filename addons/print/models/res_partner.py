
from openerp import api, models


class res_partner(models.Model):

    _inherit = "res.partner"

    @api.model
    def has_sendable_address(self):
        if not self.street:
            return False
        if not self.city:
            return False
        if not self.zip:
            return False
        if not self.country_id:
            return False
        return True

