
from openerp import api, fields, models



class print_order_wizard(models.TransientModel):

    _name = 'print.order.wizard'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_print_provider(self):
        return self.env['ir.values'].get_default('print.order', 'provider_id')

    @api.one
    @api.depends('print_order_line_wizard_ids', 'provider_id')
    def _compute_sendable(self):
        for line in self.print_order_line_wizard_ids:
            if not line.is_sendable:
                self.is_sendable = False
                return
        self.is_sendable = True

    @api.one
    @api.depends('print_order_line_wizard_ids')
    def _compute_nbr_line(self):
        self.nbr_lines = len(self.print_order_line_wizard_ids)


    # --------------------------------------------------
    # MODEL FIELDS
    # --------------------------------------------------
    is_sendable = fields.Boolean(string='Is sendable', readonly=True, compute=_compute_sendable)
    ink = fields.Selection([('BW', 'Black & White'),('CL', 'Colour')], "Ink", default='BW')
    paper = fields.Integer("Paper Weight", default=80, readonly=True)
    provider_id = fields.Many2one('print.provider', 'Print Provider', required=True, default=_default_print_provider)
    provider_balance = fields.Float("Provider Credit", digits=(16,2))
    provider_environment = fields.Selection([('test', 'Test'),('production', 'Production')], "Environment", default='test')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_default_currency)
    print_order_line_wizard_ids = fields.One2many('print.order.line.wizard', 'print_order_wizard_id', string='Lines')
    nbr_lines = fields.Integer('Number of Lines', compute=_compute_nbr_line)

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        self.provider_balance = self.provider_id.balance
        self.provider_environment = self.provider_id.environment


    # --------------------------------------------------
    # METHODS
    # --------------------------------------------------
    @api.model
    def default_get(self, fields):
        """ create the lines on the wizard """
        res = super(print_order_wizard, self).default_get(fields)

        active_ids = self._context.get('active_ids', [])
        active_model = self._context.get('active_model', False)

        if active_ids and active_model:
            # create order lines
            lines = []
            for rec in self.env[active_model].browse(active_ids):
                lines.append((0, 0, {
                    'res_id': rec.id,
                    'model_name': active_model,
                    'partner_id' : rec.partner_id.id,
                    'last_send_date' : rec.print_sent_date,
                    'is_sendable' : rec.partner_id.has_sendable_address()
                }))
            res['print_order_line_wizard_ids'] = lines
        return res


    @api.multi
    def action_apply(self):
        Print_order = self.env['print.order']
        for wizard in self:
            for line in wizard.print_order_line_wizard_ids:
                Print_order.create({
                    'ink' : wizard.ink,
                    'paper' : wizard.paper,
                    'provider_id' : wizard.provider_id.id,
                    'currency_id' : wizard.currency_id.id,
                    'user_id' : self._uid,
                    'res_id' : line.res_id,
                    'model_name' : line.model_name,
                    # duplicate partner infos
                    'partner_id' : line.partner_id.id,
                    'partner_name' : line.partner_id.name,
                    'partner_street' : line.partner_id.street,
                    'partner_street2' : line.partner_id.street2,
                    'partner_state_id' : line.partner_id.state_id.id,
                    'partner_zip' : line.partner_id.zip,
                    'partner_city' : line.partner_id.city,
                    'partner_country_id' : line.partner_id.country_id.id,
                })
        return {'type': 'ir.actions.act_window_close'}


class print_order_line_wizard(models.TransientModel):

    @api.one
    @api.depends('partner_id')
    def _compute_sendable(self):
        self.is_sendable = self.partner_id.has_sendable_address()

    _name = 'print.order.line.wizard'

    # --------------------------------------------------
    # MODEL FIELDS
    # --------------------------------------------------
    print_order_wizard_id = fields.Many2one('print.order.wizard', 'Print Order Wizard')
    res_id = fields.Integer('Object ID')
    model_name = fields.Char('Model Name')
    partner_id = fields.Many2one('res.partner', 'Recipient partner')
    last_send_date = fields.Datetime("Last Send Date", default=False)

    is_sendable = fields.Boolean(string='Is sendable', readonly=True, compute='_compute_sendable')

