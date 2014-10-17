# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

def str_to_datetime(strdate):
    return datetime.datetime.strptime(strdate, tools.DEFAULT_SERVER_DATE_FORMAT)

class fleet_vehicle_cost(models.Model):
    _name = 'fleet.vehicle.cost'
    _description = 'Cost related to a vehicle'
    _order = 'date desc, vehicle_id asc'

    @api.one
    @api.depends('odometer_id')
    def _get_odometer(self):
        self.odometer = self.odometer_id.value if self.odometer_id else 0.0

    @api.one
    def _set_odometer(self):
        if not self.odometer:
            raise except_orm(_('Operation not allowed!'), _('Emptying the odometer value of a vehicle is not allowed.'))
        odometer_id = self.env['fleet.vehicle.odometer'].create({
            'value': self.odometer,
            'date': self.date or fields.Date.today(),
            'vehicle_id': self.vehicle_id.id})
        return self.write({'odometer_id': odometer_id.id})

    name = fields.Char(related='vehicle_id.name', string='Name', store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, help='Vehicle concerned by this log')
    cost_subtype_id = fields.Many2one('fleet.service.type', string='Type', help='Cost type purchased with this cost')
    amount = fields.Float('Total Price')
    cost_type = fields.Selection(selection=[
        ('contract', 'Contract'), ('services', 'Services'), ('fuel', 'Fuel'), ('other', 'Other')],
        string='Category of the cost', help='For internal purpose only',
        required=True, default='other')
    parent_id = fields.Many2one('fleet.vehicle.cost', string='Parent', help='Parent cost to this current cost')
    cost_ids = fields.One2many('fleet.vehicle.cost', 'parent_id', string='Included Services')
    odometer_id = fields.Many2one('fleet.vehicle.odometer', string='Odometer', help='Odometer measure of the vehicle at the moment of this log')
    odometer = fields.Float(compute='_get_odometer', inverse='_set_odometer', string='Odometer Value', help='Odometer measure of the vehicle at the moment of this log')
    odometer_unit = fields.Selection(related='vehicle_id.odometer_unit', string="Unit", readonly=True)
    date = fields.Date('Date', help='Date when the cost has been executed')
    contract_id = fields.Many2one('fleet.vehicle.log.contract', string='Contract', help='Contract attached to this cost')
    auto_generated = fields.Boolean('Automatically Generated', readonly=True, required=True)

    @api.model
    def create(self, data):
        #make sure that the data are consistent with values of parent and contract records given
        if 'parent_id' in data and data['parent_id']:
            parent = self.browse(data['parent_id'])
            data['vehicle_id'] = parent.vehicle_id.id
            data['date'] = parent.date
            data['cost_type'] = parent.cost_type
        if 'contract_id' in data and data['contract_id']:
            contract = self.env['fleet.vehicle.log.contract'].browse(data['contract_id'])
            data['vehicle_id'] = contract.vehicle_id.id
            data['cost_subtype_id'] = contract.cost_subtype_id.id
            data['cost_type'] = contract.cost_type
        if 'odometer' in data and not data['odometer']:
            #if received value for odometer is 0, then remove it from the data as it would result to the creation of a
            #odometer log with 0, which is to be avoided
            del(data['odometer'])
        return super(fleet_vehicle_cost, self).create(data)

class fleet_vehicle_tag(models.Model):
    _name = 'fleet.vehicle.tag'

    name = fields.Char('Name', required=True, translate=True)

class fleet_vehicle_state(models.Model):
    _name = 'fleet.vehicle.state'
    _order = 'sequence asc'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', help="Used to order the note stages")

    _sql_constraints = [('fleet_state_name_unique','unique(name)', 'State name already exists')]


class fleet_vehicle_model(models.Model):

    @api.depends('modelname', 'brand_id')
    def _model_name_get_fnc(self):
        name = self.modelname
        if self.brand_id.name:
            name = self.brand_id.name + ' / ' + name if name else ''
        self.name = name

    @api.onchange('brand_id')
    def on_change_brand(self):
        self.image_medium = self.brand_id.image

    _name = 'fleet.vehicle.model'
    _description = 'Model of a vehicle'
    _order = 'name asc'

    name = fields.Char(compute='_model_name_get_fnc', string='Name', store=True)
    modelname = fields.Char('Model name', required=True)
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string='Make', required=True, help='Make of the vehicle')
    vendors = fields.Many2many('res.partner', 'fleet_vehicle_model_vendors', 'model_id', 'partner_id', string='Vendors')
    image = fields.Binary(related='brand_id.image', string="Logo")
    image_medium = fields.Binary(related='brand_id.image_medium', string="Logo (medium)")
    image_small = fields.Binary(related='brand_id.image_small', string="Logo (small)")


class fleet_vehicle_model_brand(models.Model):
    _name = 'fleet.vehicle.model.brand'
    _description = 'Brand model of the vehicle'

    _order = 'name asc'

    @api.depends('image')
    def _get_image(self):
        self.image_medium = tools.image_get_resized_images(self.image)['image_medium']
        self.image_small = tools.image_get_resized_images(self.image)['image_small']

    def _set_image(self, value):
        self.write({'image': tools.image_resize_image_big(value)})

    name = fields.Char('Make', required=True)
    image = fields.Binary("Logo", help="This field holds the image used as logo for the brand,limited to 1024x1024px.")
    image_medium = fields.Binary(
        compute='_get_image', inverse='_set_image',
        string="Medium-sized photo", store=True,
        help="Medium-sized logo of the brand. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        compute='_get_image', inverse='_set_image',
        string="Smal-sized photo", store=True,
        help="Small-sized photo of the brand. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")


class fleet_vehicle(models.Model):

    _inherit = 'mail.thread'

    @api.multi
    @api.depends('license_plate')
    def _vehicle_name_get_fnc(self):
        for record in self:
            if record.model_id:
                record.name = record.model_id.brand_id.name + '/' + record.model_id.modelname + ' / ' + record.license_plate
            else:
                record.name = record.license_plate

    @api.multi
    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        if self._context.get('xml_id'):
            res = self.env.ref('fleet.' + self._context['xml_id']).read()[0]
            res['context'] = self._context or {}
            res['context'] = dict(res['context'], default_vehicle_id=self[0].id)
            res['domain'] = [('vehicle_id', '=', self[0].id)]
            return res
        return False

    @api.multi
    def act_show_log_cost(self):
        """ This opens log view to view and add new log for this vehicle, groupby default to only show effective costs
            @return: the costs log view
        """
        res = self.env.ref('fleet.fleet_vehicle_costs_act').read()[0]
        res['context'] = self._context or {}
        res['context'] = dict(res['context'], default_vehicle_id=self.id, search_default_parent_false=True)
        res['domain'] = [('vehicle_id', '=', self[0].id)]
        return res

    @api.multi
    def _get_odometer(self):
        fleet_odo_obj = self.env['fleet.vehicle.odometer']
        for record in self:
            ids = fleet_odo_obj.search([('vehicle_id', '=', record.id)], limit=1, order='value desc')
            record.odometer = ids[0].value if len(ids._ids) > 0 else 0.0

    def _set_odometer(self):
        if self.odometer_count:
            date = fields.Date.today()
            data = {'value': self.odometer_count, 'date': date, 'vehicle_id': self.id}
            return self.env['fleet.vehicle.odometer'].create(data)

    @api.model
    def _search_get_overdue_contract_reminder(self, args):
        res = []
        for field, operator, value in args:
            assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
            if (operator == '=' and value == True) or (operator in ('<>', '!=') and value == False):
                search_operator = 'in'
            else:
                search_operator = 'not in'
            today = fields.Date.today()
            self._cr.execute('select cost.vehicle_id, count(contract.id) as contract_number FROM fleet_vehicle_cost cost left join fleet_vehicle_log_contract contract on contract.cost_id = cost.id WHERE contract.expiration_date is not null AND contract.expiration_date < %s AND contract.state IN (\'open\', \'toclose\') GROUP BY cost.vehicle_id', (today,))
            res_ids = [x[0] for x in self._cr.fetchall()]
            res.append(('id', search_operator, res_ids))
        return res

    @api.model
    def _search_contract_renewal_due_soon(self, args):
        res = []
        for field, operator, value in args:
            assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
            if (operator == '=' and value == True) or (operator in ('<>', '!=') and value == False):
                search_operator = 'in'
            else:
                search_operator = 'not in'
            today = fields.Date.today()
            datetime_today = datetime.datetime.strptime(today, tools.DEFAULT_SERVER_DATE_FORMAT)
            limit_date = str((datetime_today + relativedelta(days=+15)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT))
            self._cr.execute('select cost.vehicle_id, count(contract.id) as contract_number FROM fleet_vehicle_cost cost left join fleet_vehicle_log_contract contract on contract.cost_id = cost.id WHERE contract.expiration_date is not null AND contract.expiration_date > %s AND contract.expiration_date < %s AND contract.state IN (\'open\', \'toclose\') GROUP BY cost.vehicle_id', (today, limit_date))
            res_ids = [x[0] for x in self._cr.fetchall()]
            res.append(('id', search_operator, res_ids))
        return res

    @api.multi
    def _get_contract_reminder_fnc(self):
        log_cont_obj = self.env['fleet.vehicle.log.contract']
        for record in self:
            overdue = False
            due_soon = False
            total = 0
            name = ''
            for element in record.log_contracts:
                if element.state in ('open', 'toclose') and element.expiration_date:
                    current_date_str = fields.Date.today()
                    due_time_str = element.expiration_date
                    current_date = str_to_datetime(current_date_str)
                    due_time = str_to_datetime(due_time_str)
                    diff_time = (due_time-current_date).days
                    if diff_time < 0:
                        overdue = True
                        total += 1
                    if diff_time < 15 and diff_time >= 0:
                            due_soon = True
                            total += 1
                    if overdue or due_soon:
                        ids = log_cont_obj.search([('vehicle_id', '=', record.id), ('state', 'in', ('open', 'toclose'))], limit=1, order='expiration_date asc')
                        if len(ids._ids) > 0:
                            #we display only the name of the oldest overdue/due soon contract
                            name = (ids[0].cost_subtype_id.name)

            record.contract_renewal_overdue = overdue
            record.contract_renewal_due_soon = due_soon
            record.contract_renewal_total = (total - 1)  #we remove 1 from the real total for display purposes
            record.contract_renewal_name = name

    @api.model
    def _get_default_state(self):
        try:
            model_id = self.env.ref('fleet', 'vehicle_state_active').id
        except ValueError:
            model_id = False
        return model_id

    @api.multi
    def _count_all(self):
        Odometer = self.env['fleet.vehicle.odometer']
        LogFuel = self.env['fleet.vehicle.log.fuel']
        LogService = self.env['fleet.vehicle.log.services']
        LogContract = self.env['fleet.vehicle.log.contract']
        Cost = self.env['fleet.vehicle.cost']
        for vehicle_id in self:
            vehicle_id.odometer_count = Odometer.search_count([('vehicle_id', '=', vehicle_id.id)])
            vehicle_id.fuel_logs_count = LogFuel.search_count([('vehicle_id', '=', vehicle_id.id)])
            vehicle_id.service_count = LogService.search_count([('vehicle_id', '=', vehicle_id.id)])
            vehicle_id.contract_count = LogContract.search_count([('vehicle_id', '=', vehicle_id.id)])
            vehicle_id.cost_count = Cost.search_count([('vehicle_id', '=', vehicle_id.id), ('parent_id', '=', False)])

    _name = 'fleet.vehicle'
    _description = 'Information on a vehicle'
    _order = 'license_plate asc'

    name = fields.Char(compute='_vehicle_name_get_fnc', string='Name', store=True)
    company_id = fields.Many2one('res.company', string='Company')
    license_plate = fields.Char('License Plate', required=True, help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)', copy=False)
    driver_id = fields.Many2one('res.partner', string='Driver', help='Driver of the vehicle')
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', required=True, help='Model of the vehicle')
    log_fuel = fields.One2many('fleet.vehicle.log.fuel', 'vehicle_id', string='Fuel Logs')
    log_services = fields.One2many('fleet.vehicle.log.services', 'vehicle_id', string='Services Logs')
    log_contracts = fields.One2many('fleet.vehicle.log.contract', 'vehicle_id', string='Contracts')
    cost_count = fields.Integer(compute='_count_all', string="Costs")
    contract_count = fields.Integer(compute='_count_all', string='Contracts')
    service_count = fields.Integer(compute='_count_all', string='Services')
    fuel_logs_count = fields.Integer(compute='_count_all', string='Fuel Logs')
    odometer_count = fields.Integer(compute='_count_all', string='Odometer')
    acquisition_date = fields.Date('Acquisition Date', required=False, help='Date when the vehicle has been bought')
    color = fields.Char('Color', help='Color of the vehicle')
    state_id = fields.Many2one('fleet.vehicle.state', string='State', help='Current state of the vehicle', ondelete="set null", default=_get_default_state)
    location = fields.Char('Location', help='Location of the vehicle (garage, ...)')
    seats = fields.Integer('Seats Number', help='Number of seats of the vehicle')
    doors = fields.Integer('Doors Number', help='Number of doors of the vehicle', default=5)
    tag_ids = fields.Many2many('fleet.vehicle.tag', 'fleet_vehicle_vehicle_tag_rel', 'vehicle_tag_id', 'tag_id', string='Tags', copy=False)
    odometer = fields.Float(compute='_get_odometer', inverse='_set_odometer', string='Last Odometer', help='Odometer measure of the vehicle at the moment of this log')
    odometer_unit = fields.Selection(selection=[
        ('kilometers', 'Kilometers'),
        ('miles', 'Miles')],
        string='Odometer Unit', help='Unit of the odometer', required=True, default='kilometers')
    transmission = fields.Selection(selection=[('manual', 'Manual'), ('automatic', 'Automatic')], string='Transmission', help='Transmission Used by the vehicle')
    fuel_type = fields.Selection(selection=[('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], string='Fuel Type', help='Fuel Used by the vehicle')
    horsepower = fields.Integer('Horsepower')
    horsepower_tax = fields.Float('Horsepower Taxation')
    power = fields.Integer('Power', help='Power in kW of the vehicle')
    co2 = fields.Float('CO2 Emissions', help='CO2 emissions of the vehicle')
    image = fields.Binary(related='model_id.image', string="Logo")
    image_medium = fields.Binary(related='model_id.image_medium', string="Logo (medium)")
    image_small = fields.Binary(related='model_id.image_small', string="Logo (small)")
    contract_renewal_due_soon = fields.Boolean(compute='_get_contract_reminder_fnc', search='_search_contract_renewal_due_soon', string='Has Contracts to renew')
    contract_renewal_overdue = fields.Boolean(compute='_get_contract_reminder_fnc', search='_search_get_overdue_contract_reminder', string='Has Contracts Overdued')
    contract_renewal_name = fields.Text(compute='_get_contract_reminder_fnc', string='Name of contract to renew soon')
    contract_renewal_total = fields.Integer(compute='_get_contract_reminder_fnc', string='Total of contracts due or overdue minus one')
    car_value = fields.Float('Car Value', help='Value of the bought vehicle')

    @api.onchange('model_id')
    def on_change_model(self):
        self.image_medium = self.model_id.image

    @api.model
    def create(self, data):
        vehicle_id = super(fleet_vehicle, self).create(data)
        vehicle_id.message_post(body=_('%s %s has been added to the fleet!') % (vehicle_id.model_id.name, vehicle_id.license_plate))
        return vehicle_id

    @api.multi
    def write(self, vals):
        """
        This function write an entry in the openchatter whenever we change important information
        on the vehicle like the model, the drive, the state of the vehicle or its license plate
        """
        for vehicle in self:
            changes = []
            if 'model_id' in vals and vehicle.model_id.id != vals['model_id']:
                value = self.env['fleet.vehicle.model'].browse(vals['model_id']).name
                oldmodel = vehicle.model_id.name or _('None')
                changes.append(_("Model: from '%s' to '%s'") % (oldmodel, value))
            if 'driver_id' in vals and vehicle.driver_id.id != vals['driver_id']:
                value = self.env['res.partner'].browse(vals['driver_id']).name
                olddriver = (vehicle.driver_id.name) or _('None')
                changes.append(_("Driver: from '%s' to '%s'") % (olddriver, value))
            if 'state_id' in vals and vehicle.state_id.id != vals['state_id']:
                value = self.env['fleet.vehicle.state'].browse(vals['state_id']).name
                oldstate = vehicle.state_id.name or _('None')
                changes.append(_("State: from '%s' to '%s'") % (oldstate, value))
            if 'license_plate' in vals and vehicle.license_plate != vals['license_plate']:
                old_license_plate = vehicle.license_plate or _('None')
                changes.append(_("License Plate: from '%s' to '%s'") % (old_license_plate, vals['license_plate']))

            if len(changes) > 0:
                vehicle.message_post(body=", ".join(changes))
        return super(fleet_vehicle, self).write(vals)


class fleet_vehicle_odometer(models.Model):
    _name = 'fleet.vehicle.odometer'
    _description = 'Odometer log for a vehicle'
    _order = 'date desc'

    @api.depends('vehicle_id')
    def _vehicle_log_name_get_fnc(self):
        name = self.vehicle_id.name if self.vehicle_id.name else ''
        if self.date:
            name = name + ' / ' + str(self.date)
        self.name = name

    @api.onchange('vehicle_id')
    def on_change_vehicle(self):
        self.unit = self.vehicle_id.odometer_unit

    name = fields.Char(compute='_vehicle_log_name_get_fnc', string='Name', store=True)
    date = fields.Date('Date', default=fields.Date.today())
    value = fields.Float('Odometer Value', group_operator="max")
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    unit = fields.Selection(related='vehicle_id.odometer_unit', string="Unit", readonly=True)


class fleet_vehicle_log_fuel(models.Model):

    @api.onchange('vehicle_id')
    def on_change_vehicle(self):
        self.odometer_unit = self.vehicle_id.odometer_unit
        self.purchaser_id = self.vehicle_id.driver_id

    @api.onchange('liter', 'price_per_liter', 'amount')
    def on_change_liter(self):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if liter > 0 and price_per_liter > 0 and round(liter*price_per_liter, 2) != amount:
            self.amount = round(liter * price_per_liter, 2)
        elif amount > 0 and liter > 0 and round(amount/liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter, 2) != liter:
            self.liter = round(amount / price_per_liter, 2)

    @api.onchange('price_per_liter')
    def on_change_price_per_liter(self):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if liter > 0 and price_per_liter > 0 and round(liter*price_per_liter, 2) != amount:
            self.amount = round(liter * price_per_liter, 2)
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter, 2) != liter:
            self.liter = round(amount / price_per_liter, 2)
        elif amount > 0 and liter > 0 and round(amount/liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)

    @api.onchange('amount')
    def on_change_amount(self):
        #need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        #make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        #liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        #of 3.0/2=1.5)
        #If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        #onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        #computation to 2 decimal
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if amount > 0 and liter > 0 and round(amount/liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)
        elif amount > 0 and price_per_liter > 0 and round(amount/price_per_liter, 2) != liter:
            self.liter = round(amount / price_per_liter, 2)
        elif liter > 0 and price_per_liter > 0 and round(liter*price_per_liter, 2) != amount:
            self.amount = round(liter * price_per_liter, 2)

    @api.v7
    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_refueling')
        except ValueError:
            model_id = False
        return model_id

    _name = 'fleet.vehicle.log.fuel'
    _description = 'Fuel log for vehicles'
    _inherits = {'fleet.vehicle.cost': 'cost_id'}

    liter = fields.Float('Liter')
    price_per_liter = fields.Float('Price Per Liter')
    purchaser_id = fields.Many2one('res.partner', string='Purchaser', domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference', size=64)
    vendor_id = fields.Many2one('res.partner', string='Supplier', domain="[('supplier','=',True)]")
    notes = fields.Text('Notes')
    cost_id = fields.Many2one('fleet.vehicle.cost', string='Cost', required=True, ondelete='cascade')
    cost_amount = fields.Float(related='cost_id.amount', string='Amount', store=True) #we need to keep this field as a related with store=True because the graph view doesn't support (1) to address fields from inherited table and (2) fields that aren't stored in database

    _defaults = {
        'date': fields.Date.today(),
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'fuel',
    }


class fleet_vehicle_log_services(models.Model):

    @api.onchange('vehicle_id')
    def on_change_vehicle(self):
        self.odometer_unit = self.vehicle_id.odometer_unit
        self.purchaser_id = self.vehicle_id.driver_id

    @api.v7
    def _get_default_service_type(self, cr, uid, context):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_service_service_8')
        except ValueError:
            model_id = False
        return model_id

    _inherits = {'fleet.vehicle.cost': 'cost_id'}
    _name = 'fleet.vehicle.log.services'
    _description = 'Services for vehicles'

    purchaser_id = fields.Many2one('res.partner', string='Purchaser', domain="['|',('customer','=',True),('employee','=',True)]")
    inv_ref = fields.Char('Invoice Reference')
    vendor_id = fields.Many2one('res.partner', string='Supplier', domain="[('supplier','=',True)]")
    cost_amount = fields.Float(related='cost_id.amount', string='Amount', store=True) #we need to keep this field as a related with store=True because the graph view doesn't support (1) to address fields from inherited table and (2) fields that aren't stored in database
    notes = fields.Text('Notes')
    cost_id = fields.Many2one('fleet.vehicle.cost', string='Cost', required=True, ondelete='cascade')

    _defaults = {
        'date': fields.Date.today(),
        'cost_subtype_id': _get_default_service_type,
        'cost_type': 'services'
    }


class fleet_service_type(models.Model):
    _name = 'fleet.service.type'
    _description = 'Type of services available on a vehicle'

    name = fields.Char('Name', required=True, translate=True)
    category = fields.Selection(selection=[
        ('contract', 'Contract'),
        ('service', 'Service'),
        ('both', 'Both')],
        string='Category', required=True, help='Choose wheter the service refer to contracts, vehicle services or both')


class fleet_vehicle_log_contract(models.Model):

    @api.model
    def scheduler_manage_auto_costs(self):
        #This method is called by a cron task
        #It creates costs for contracts having the "recurring cost" field setted, depending on their frequency
        #For example, if a contract has a reccuring cost of 200 with a weekly frequency, this method creates a cost of 200 on the first day of each week, from the date of the last recurring costs in the database to today
        #If the contract has not yet any recurring costs in the database, the method generates the recurring costs from the start_date to today
        #The created costs are associated to a contract thanks to the many2one field contract_id
        #If the contract has no start_date, no cost will be created, even if the contract has recurring costs
        vehicle_cost_obj = self.env['fleet.vehicle.cost']
        d = datetime.datetime.strptime(fields.Date.today(), tools.DEFAULT_SERVER_DATE_FORMAT)
        contract_ids = self.env['fleet.vehicle.log.contract'].search([('state', '!=', 'closed')])
        deltas = {'yearly': relativedelta(years=+1), 'monthly': relativedelta(months=+1), 'weekly': relativedelta(weeks=+1), 'daily': relativedelta(days=+1)}
        for contract in contract_ids:
            if not contract.start_date or contract.cost_frequency == 'no':
                continue
            found = False
            last_cost_date = contract.start_date
            if contract.generated_cost_ids:
                last_autogenerated_cost = vehicle_cost_obj.search(['&', ('contract_id', '=', contract.id), ('auto_generated', '=', True)], order='date desc')[0]
                if last_autogenerated_cost:
                    found = True
                    last_cost_date = last_autogenerated_cost.date
            startdate = datetime.datetime.strptime(last_cost_date, tools.DEFAULT_SERVER_DATE_FORMAT)
            if found:
                startdate += deltas.get(contract.cost_frequency)
            while (startdate <= d) and (startdate <= datetime.datetime.strptime(contract.expiration_date, tools.DEFAULT_SERVER_DATE_FORMAT)):
                data = {
                    'amount': contract.cost_generated,
                    'date': startdate.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                    'vehicle_id': contract.vehicle_id.id,
                    'cost_subtype_id': contract.cost_subtype_id.id,
                    'contract_id': contract.id,
                    'auto_generated': True
                }
                self.env['fleet.vehicle.cost'].create(data)
                startdate += deltas.get(contract.cost_frequency)
        return True

    @api.model
    def scheduler_manage_contract_expiration(self):
        #This method is called by a cron task
        #It manages the state of a contract, possibly by posting a message on the vehicle concerned and updating its status
        datetime_today = datetime.datetime.strptime(fields.Date.today(), tools.DEFAULT_SERVER_DATE_FORMAT)
        limit_date = (datetime_today + relativedelta(days=+15)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        ids = self.search(['&', ('state', '=', 'open'), ('expiration_date', '<', limit_date)])
        from collections import defaultdict
        res = defaultdict(int)
        for contract in ids:
                res[contract.vehicle_id.id] += 1
        for vehicle, value in res.items():
            self.env['fleet.vehicle'].browse(vehicle).message_post(body=_('%s contract(s) need(s) to be renewed and/or closed!') % (str(value)))
        return self.write({'state': 'toclose'})

    @api.model
    def run_scheduler(self):
        self.scheduler_manage_auto_costs()
        self.scheduler_manage_contract_expiration()
        return True

    @api.multi
    @api.depends('cost_subtype_id')
    def _vehicle_contract_name_get_fnc(self):
        for record in self:
            name = record.vehicle_id.name if record.vehicle_id else ''
            if record.cost_subtype_id and record.cost_subtype_id.name:
                name += ' / ' + record.cost_subtype_id.name
            if record.date:
                name += ' / ' + record.date
            record.name = name

    @api.onchange('vehicle_id')
    def on_change_vehicle(self):
        self.odometer_unit = self.vehicle_id.odometer_unit

    @api.returns('fleet_vehicle_log_contract')
    def compute_next_year_date(self, strdate):
        oneyear = datetime.timedelta(days=365)
        curdate = str_to_datetime(strdate)
        return datetime.datetime.strftime(curdate + oneyear, tools.DEFAULT_SERVER_DATE_FORMAT)

    @api.one
    def on_change_start_date(self, strdate, enddate):
        if (strdate):
            self.expiration_date = self.compute_next_year_date(strdate)

    @api.multi
    def get_days_left(self):
        """return a dict with as value for each contract an integer
        if contract is in an open state and is overdue, return 0
        if contract is in a closed state, return -1
        otherwise return the number of days before the contract expires
        """
        for record in self:
            if (record.expiration_date and (record.state in ('open', 'toclose'))):
                today = str_to_datetime(time.strftime(tools.DEFAULT_SERVER_DATE_FORMAT))
                renew_date = str_to_datetime(record.expiration_date)
                diff_time = (renew_date-today).days
                record.days_left = diff_time > 0 and diff_time or 0
            else:
                record.days_left = -1

    @api.one
    def act_renew_contract(self):
        assert len(self._ids) == 1, "This operation should only be done for 1 single contract at a time, as it it suppose to open a window as result"
        #compute end date
        startdate = str_to_datetime(self.start_date)
        enddate = str_to_datetime(self.expiration_date)
        diffdate = (enddate - startdate)
        default = {
            'date': fields.Date.today(),
            'start_date': datetime.datetime.strftime(str_to_datetime(self.expiration_date) + datetime.timedelta(days=1), tools.DEFAULT_SERVER_DATE_FORMAT),
            'expiration_date': datetime.datetime.strftime(enddate + diffdate, tools.DEFAULT_SERVER_DATE_FORMAT),
        }
        newid = self.copy(default).id
        return {
            'name': _("Renew Contract"),
            'view_mode': 'form',
            'view_id': self.env.ref('fleet.fleet_vehicle_log_contract_form').id,
            'view_type': 'tree,form',
            'res_model': 'fleet.vehicle.log.contract',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'res_id': newid,
            'context': {'active_id': newid},
        }

    @api.v7
    def _get_default_contract_type(self, cr, uid, context=None):
        try:
            model, model_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'fleet', 'type_contract_leasing')
        except ValueError:
            model_id = False
        return model_id

    @api.onchange('cost_ids')
    def on_change_indic_cost(self):
        self.sum_cost = sum(element.amount for element in self.cost_ids)

    @api.multi
    def _get_sum_cost(self):
        for contract in self:
            contract.sum_cost = sum(cost.amount for cost in contract.cost_ids)

    _inherits = {'fleet.vehicle.cost': 'cost_id'}
    _name = 'fleet.vehicle.log.contract'
    _description = 'Contract information on a vehicle'
    _order = 'state desc, expiration_date'

    name = fields.Text(compute='_vehicle_contract_name_get_fnc', string='Name', store=True)
    start_date = fields.Date('Contract Start Date', help='Date when the coverage of the contract begins', default=fields.Date.today())
    expiration_date = fields.Date(
        'Contract Expiration Date',
        default=lambda self: self.compute_next_year_date(fields.Date.today()),
        help='Date when the coverage of the contract expirates (by default, one year after begin date)')
    days_left = fields.Integer(compute='get_days_left', string='Warning Date')
    insurer_id = fields.Many2one('res.partner', string='Supplier')
    purchaser_id = fields.Many2one(
        'res.partner', string='Contractor', help='Person to which the contract is signed for',
        default=lambda self: self.env['res.users'].browse(self._uid).partner_id.id or False)
    ins_ref = fields.Char('Contract Reference', copy=False)
    state = fields.Selection(
        selection=[('open', 'In Progress'), ('toclose', 'To Close'), ('closed', 'Terminated')],
        string='Status', readonly=True, help='Choose wheter the contract is still valid or not',
        copy=False, default='open')
    notes = fields.Text('Terms and Conditions', help='Write here all supplementary informations relative to this contract', copy=False)
    cost_generated = fields.Float('Recurring Cost Amount', help="Costs paid at regular intervals, depending on the cost frequency. If the cost frequency is set to unique, the cost will be logged at the start date")
    cost_frequency = fields.Selection(
        selection=[('no', 'No'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        string='Recurring Cost Frequency', help='Frequency of the recuring cost', required=True,
        default='no')
    generated_cost_ids = fields.One2many('fleet.vehicle.cost', 'contract_id', string='Generated Costs')
    sum_cost = fields.Float(compute='_get_sum_cost', string='Indicative Costs Total')
    cost_id = fields.Many2one('fleet.vehicle.cost', string='Cost', required=True, ondelete='cascade')
    cost_amount = fields.Float(related='cost_id.amount', string='Amount', store=True) #we need to keep this field as a related with store=True because the graph view doesn't support (1) to address fields from inherited table and (2) fields that aren't stored in database

    _defaults = {
        'date': fields.Date.today(),
        'cost_subtype_id': _get_default_contract_type,
        'cost_type': 'contract',
    }

    @api.multi
    def contract_close(self):
        return self.write({'state': 'closed'})

    @api.multi
    def contract_open(self):
        return self.write({'state': 'open'})

class fleet_contract_state(models.Model):
    _name = 'fleet.contract.state'
    _description = 'Contains the different possible status of a leasing contract'

    name = fields.Char('Contract Status', required=True)
