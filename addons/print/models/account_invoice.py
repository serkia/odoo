
from openerp import api, fields, models
from openerp.tools.translate import _


class account_invoice(models.Model):
    """ Printable account_invoice. Do not rename field or method name, since they are called by
        print.provider and print.order.wizard, and they obey to the naming convention.
        Every printable model must have these fields/methods.
    """

    _inherit = ['account.invoice']

    print_sent_date = fields.Datetime("Last Postal Sent Date", default=False)

    @api.multi
    def print_validate_sending(self, print_order_id):
        order = self.env['print.order'].browse(print_order_id)
        for record in self:
            # save sending data
            record.write({
                'print_sent_date' : fields.Datetime.now(),
                'sent' : True
            })
            # put confirmation message in the chatter
            message = _("This invoice was sent by post with the provider <i>%s</i> at the following address. <br/><br/> \
                         %s <br/> %s <br/> %s %s<br/>%s") % (order.provider_id.name, order.partner_name, order.partner_street, order.partner_city, order.partner_zip, order.partner_country_id.name)
            record.sudo(user=order.user_id.id).message_post(body=message)

