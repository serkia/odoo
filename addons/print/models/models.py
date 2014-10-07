import base64
import re
import time

from openerp import api, fields, models
from openerp.tools.translate import _


class print_provider(models.Model):
    """ Print Provider Base Model. Each specific provider can extend the model by adding
        its own fields, using the provider_name (provider field) as a prefix for the new
        fields and method.
    """

    _name = 'print.provider'
    _rec_name = 'name'
    _description = 'Postal Provider'


    @api.model
    def _get_providers(self):
        return []

    # --------------------------------------------------
    # MODEL FIELDS
    # --------------------------------------------------
    name = fields.Char("Name", required=True)
    environment = fields.Selection([('test', 'Test'),('production', 'Production')], "Environment", default='test')
    provider = fields.Selection(selection='_get_providers', string='Provider', required=True)
    balance = fields.Float("Credit", digits=(16,2))


    # --------------------------------------------------
    # METHOD to be redefine in the provider implemenation
    # --------------------------------------------------
    @api.one
    def update_account_data(self):
        """ Update the provider account data. Requires a fetch to the provider server. """
        if hasattr(self, '%s_update_account_data' % self.provider):
            return getattr(self, '%s_update_account_data' % self.provider)()


class print_order(models.Model):
    """ Print Order Model. Each specific provider can extend the model by adding
        its own fields, using the same convertion of the print.provider model.
    """

    _name = 'print.order'
    _rec_name = 'id'
    _description = 'Postal Order'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_print_provider(self):
        return self.env['ir.values'].get_default('print.order', 'provider_id')

    # --------------------------------------------------
    # MODEL FIELDS
    # --------------------------------------------------
    create_date = fields.Datetime('Create Date', readonly=True)
    send_date = fields.Datetime('Sent Date', default=False, readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_default_currency, readonly=True, states={'draft':[('readonly',False)]})
    user_id = fields.Many2one('res.users', 'Author', default=lambda self: self.env.user, readonly=True)
    provider_id = fields.Many2one('print.provider', 'Print Provider', required=True, default=_default_print_provider, readonly=True, states={'draft':[('readonly',False)]})

    ink = fields.Selection([('BW', 'Black & White'),('CL', 'Colour')], "Ink", default='BW', states={'sent':[('readonly',True)]})
    paper = fields.Integer("Paper Weight", default=80, readonly=True)
    res_id = fields.Integer('Object ID', readonly=True)
    model_name = fields.Char('Model Name', readonly=True)

    attachment_id = fields.Many2one('ir.attachment', 'PDF', readonly=True)
    nbr_pages = fields.Integer("Number of Pages", readonly=True, default=0)
    price = fields.Float("Cost to Deliver", digits=(16,2), readonly=True, default=0.0)

    error_message = fields.Text('Error Message', readonly=True)

    state = fields.Selection([
            ('draft', 'Draft'),
            ('ready_to_send', 'Ready'),
            ('sent', 'Sent'),
            ('error', 'Failed'),
        ], string='Status', default='draft', readonly=True, required=True)

    # duplicate partner infos to keep trace of where the documents was sent
    partner_id = fields.Many2one('res.partner', 'Recipient partner', states={'sent':[('readonly',True)]})
    partner_name = fields.Char('Name', required=True, states={'sent':[('readonly',True)]})
    partner_street = fields.Char('Street', required=True, states={'sent':[('readonly',True)]})
    partner_street2 = fields.Char('Street2', states={'sent':[('readonly',True)]})
    partner_state_id = fields.Many2one("res.country.state", 'State', states={'sent':[('readonly',True)]})
    partner_zip = fields.Char('Zip', required=True, states={'sent':[('readonly',True)]})
    partner_city = fields.Char('City', required=True, states={'sent':[('readonly',True)]})
    partner_country_id = fields.Many2one('res.country', 'Country', required=True, states={'sent':[('readonly',True)]})


    # --------------------------------------------------
    # Methods
    # --------------------------------------------------
    @api.model
    def _group_by_provider(self, orders):
        """ Group the order id by provider. This will return a dict where
            the key is the provider id, and the value is a list of order_ids.
            :param list orders : recordset of order to group by provider
            :return dict :  key is the provider id
                            value is a list of order ids
        """
        # Optimization : group the print orders by provider. Each
        # provider will have its list of order ids to treat.
        group_by_provider = {}
        for order in orders:
            if not order.provider_id.id in group_by_provider:
                group_by_provider[order.provider_id.id] = []
            group_by_provider[order.provider_id.id].append(order.id)
        return group_by_provider

    @api.model
    def _count_pages_pdf(self, pdf):
        """ Count the number of pages of the given pdf file.
            :param pdf : base64 code of the pdf file
        """
        pages = 0
        for match in re.compile(r"/Count\s+(\d+)").finditer(pdf):
            pages = int(match.group(1))
        return pages

    @api.multi
    def action_generate_report(self, force=False):
        """ Generate PDF report and compute its number of pages for the given recordset.
            :param boolean force :  True will force the generation of the PDF, even if it was
                                    already generated. Default is False.
        """
        for rec in self:
            if not rec.attachment_id or force:
                record_to_print = self.env[rec.model_name].browse([rec.res_id])[0]

                values = {}

                Attachment = self.env['ir.attachment']
                attachment_id = False
                # check if a report exists for current res_model
                report = self.env['ir.actions.report.xml'].search([('model', '=', rec.model_name)], limit=1)

                if report:
                    # check if the report can be reload from its ir_attachment
                    if report.attachment_use:
                        # search an existing ir_attachment for the current object
                        attachments = Attachment.search([('res_model', '=', rec.model_name), ('res_id', '=', rec.res_id)])
                        if len(attachments) >= 1:
                            attachment_id = attachments[-1].id # take the last one
                            values.update({
                                'nbr_pages' : self._count_pages_pdf(base64.b64decode(attachments[-1].datas))
                            })
                    # create a new ir_attachment for the current object if it doesn't already exist
                    if not attachment_id:
                        filename = '%s-%s' % (rec.model_name.replace(".", "_"),rec.res_id)
                        if report.attachment:
                            filename = eval(report.attachment, {'object': record_to_print, 'time': time})
                        # Call the v7 version without context (!important) to avoid "'update' not supported on frozendict".
                        # TODO : when report.py in v8, change this call (and test it !)
                        pdf = self.pool['report'].get_pdf(self._cr, self._uid, record_to_print.ids, report.report_name)
                        values.update({
                            'nbr_pages' : self._count_pages_pdf(pdf)
                        })
                        if report.attachment_use:
                            # the get_pdf method has save the pdf in an attachment
                            attachments = Attachment.search([('res_model', '=', rec.model_name), ('res_id', '=', rec.res_id)])
                            attachment_id = attachments[-1].id
                        else:
                            # create the new ir_attachment
                            attachment_value = {
                                'name': filename,
                                'res_name': filename,
                                'res_model': rec.model_name,
                                'res_id': rec.res_id,
                                'datas': base64.b64encode(pdf),
                                'datas_fname': filename+'.pdf',
                            }
                            new_attachment = Attachment.create(attachment_value)
                            attachment_id = new_attachment.id
                    # save values
                    values['attachment_id'] = attachment_id
                    rec.write(values)
                else:
                    rec.write({'error_message' : _('The document you want to print and send is not printable. There is no report action for the model %s.') % (rec.model_name,)})

    @api.multi
    def action_compute_price(self):
        """ Compute the price of the delivery. """
        for rec in self:
            if rec.state != 'ready':
                rec.action_prepare()
            # call the provider implementation
            if hasattr(rec, '%s_action_compute_price' % rec.provider_id.provider):
                getattr(rec, '%s_action_compute_price' % rec.provider_id.provider)()

    @api.multi
    def action_prepare(self):
        """ Prepare the orders for delivery. It executes the operations to put
            them into the 'ready' state.
            Self must be print.order having the same provider, to stay the optimized.
            To allow optimizations in the provider implementation, the orders
            are grouped by provider.
        """
        # generate PDF for the recordset
        for rec in self:
            if rec.state != 'ready':
                rec.action_generate_report()
        # call provider implementation
        provider_name = self[0].provider_id.provider
        if hasattr(self, '%s_action_prepare' % provider_name):
                getattr(self, '%s_action_prepare' % provider_name)()

    @api.multi
    def action_deliver(self):
        """ Send the orders for delivery to the Provider. It executes the operations to put
            them into the 'sent' state.
            Self must be print.order having the same provider, to stay the optimized.
            :return a dict, containing for each order, informations about its sending. (error_message is not mandatory)
                    {
                        'order_id' : [order.user_id, bool('correctly send'), error_message],
                    }
        """
        # only treat the orders ready to be sent
        orders_ids = [p.id for p in self if p.state == 'ready_to_send']
        orders = self.browse(orders_ids)

        result = {}
        if len(orders) > 0:
            # call provider implementation
            provider_name = orders[0].provider_id.provider
            if hasattr(orders, '%s_action_deliver' % provider_name):
                result.update(getattr(orders, '%s_action_deliver' % provider_name)())
            # if the sending is successful, apply object method on printable object to change its state, send mail, ...
            for rec in orders:
                obj = self.env[rec.model_name].browse(rec.res_id)
                if result.get(rec.id, False) and hasattr(obj, 'print_validate_sending'):
                    obj.print_validate_sending(rec.id)
        return result

    @api.model
    def process_order_queue(self, order_ids=None):
        """ Immediately send the queue, or the list of given order_ids.
            If the sending failed, it send a mail_message to the author of the print order, and the PO state
            is set to 'error'. If sending is successful, the state will be 'sent'.
            This method is call by the sendnow wizard, but also by the ir_cron.
            :param order_ids : optinal list of order ids
        """
        # find ids if not given
        if not order_ids:
            orders = self.search([('state', '!=', 'sent')])
        else:
            orders = self.browse(order_ids)
        # process Print Orders
        # recordset grouped by provider
        result = {}
        grouped_order_ids = self._group_by_provider(orders)
        for provider_id in grouped_order_ids.keys():
            current_orders = self.browse(grouped_order_ids[provider_id])
            current_orders.action_prepare()
            result.update(current_orders.action_deliver())

        # transform the dict result into another dict where
        #   key = user_id
        #   value = list of tuple (order_id, error_message) for all order not sent correctly
        user_to_notify = {}
        for order_id in result:
            if not result[order_id][1]: # if not correctly sent
                if not result[order_id][0] in user_to_notify: # if userid not already in user_to_notify
                    user_to_notify[result[order_id][0]] = []
                user_to_notify[result[order_id][0]].append((order_id, result[order_id][2]))

        # send a message to the author of the failed print orders
        Mail_message = self.env['mail.message']
        for user in self.env['res.users'].browse(user_to_notify.keys()):
            errors = ["   %s      |  %s" % (code, msg) for code, msg in  user_to_notify[user.id]]
            body = _("Dear %s,<br/> \
                    Some print orders was not sent during the last processing. Please, check \
                    the following errors, and correct them. You can find them in Settings > Print Orders. <br/><br/> \
                     Print Order ID  |      Error Message <br/>\
                    ----------------------------------------- <br/>\
                     %s") % (user.partner_id.name, "<br/>".join(errors))
            Mail_message.sudo().create({
                'body' : body,
                'subject' : _("Print Orders Failed"),
                'partner_ids': [(4, user.partner_id.id)]
            })
