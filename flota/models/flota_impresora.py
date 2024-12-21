# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.flota.models.flota_impresora_model import FUEL_TYPES


#Some fields don't have the exact same name
MODEL_FIELDS_TO_VEHICLE = {
    'transmission': 'transmission', 'model_year': 'model_year', 'electric_assistance': 'electric_assistance',
    'color': 'color', 'seats': 'seats', 'doors': 'doors', 'trailer_hook': 'trailer_hook',
    'default_co2': 'co2', 'co2_standard': 'co2_standard', 'default_fuel_type': 'fuel_type',
    'power': 'power', 'horsepower': 'horsepower', 'horsepower_tax': 'horsepower_tax', 'category_id': 'category_id',
    'impresora_range': 'impresora_range', 'power_unit': 'power_unit'
}

class FlotaImpresora(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _name = 'flota.impresora'
    _description = 'Impresora'
    _order = 'license_plate asc, acquisition_date asc'
    _rec_names_search = ['name', 'driver_id.name']

    def _get_default_state(self):
        state = self.env.ref('flota.flota_impresora_state_new_request', raise_if_not_found=False)
        return state if state and state.id else False

    name = fields.Char(compute="_compute_impresora_name", store=True)
    description = fields.Html("Impresora Description")
    active = fields.Boolean('Active', default=True, tracking=True)
    manager_id = fields.Many2one(
        'res.users', 'Flota Manager',
        domain=lambda self: [('groups_id', 'in', self.env.ref('flota.flota_group_manager').id), ('company_id', 'in', self.env.companies.ids)],
    )
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    country_id = fields.Many2one('res.country', related='company_id.country_id')
    country_code = fields.Char(related='country_id.code', depends=['country_id'])
    license_plate = fields.Char(tracking=True,
        help='License plate number of the impresora (i = plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the impresora motor (VIN/SN number)', copy=False)
    trailer_hook = fields.Boolean(default=False, string='Trailer Hitch', compute='_compute_model_fields', store=True, readonly=False)
    driver_id = fields.Many2one('res.partner', 'Driver', tracking=True, help='Driver address of the impresora', copy=False)
    future_driver_id = fields.Many2one('res.partner', 'Future Driver', tracking=True, help='Next Driver Address of the impresora', copy=False, check_company=True)
    model_id = fields.Many2one('flota.impresora.model', 'Model',
        tracking=True, required=True)
    brand_id = fields.Many2one('flota.impresora.model.brand', 'Brand', related="model_id.brand_id", store=True, readonly=False)
    log_drivers = fields.One2many('flota.impresora.assignation.log', 'impresora_id', string='Assignment Logs')
    log_services = fields.One2many('flota.impresora.log.services', 'impresora_id', 'Services Logs')
    log_contracts = fields.One2many('flota.impresora.log.contract', 'impresora_id', 'Contracts')
    contract_count = fields.Integer(compute="_compute_count_all", string='Contract Count')
    service_count = fields.Integer(compute="_compute_count_all", string='Services')
    odometer_count = fields.Integer(compute="_compute_count_all", string='Odometer')
    history_count = fields.Integer(compute="_compute_count_all", string="Drivers History Count")
    next_assignation_date = fields.Date('Assignment Date', help='This is the date at which the car will be available, if not set it means available instantly')
    order_date = fields.Date('Order Date')
    acquisition_date = fields.Date('Registration Date', required=False,
        default=fields.Date.today, help='Date of impresora registration')
    write_off_date = fields.Date('Cancellation Date', tracking=True, help="Date when the impresora's license plate has been cancelled/removed.")
    first_contract_date = fields.Date(string="First Contract Date", default=fields.Date.today)
    color = fields.Char(help='Color of the impresora', compute='_compute_model_fields', store=True, readonly=False)
    state_id = fields.Many2one('flota.impresora.state', 'State',
        default=_get_default_state, group_expand='_read_group_expand_full',
        tracking=True,
        help='Current state of the impresora', ondelete="set null")
    location = fields.Char(help='Location of the impresora (garage, ...)')
    seats = fields.Integer('Seats Number', help='Number of seats of the impresora', compute='_compute_model_fields', store=True, readonly=False)
    model_year = fields.Char('Model Year', help='Year of the model', compute='_compute_model_fields', store=True, readonly=False)
    doors = fields.Integer('Doors Number', help='Number of doors of the impresora', compute='_compute_model_fields', store=True, readonly=False)
    tag_ids = fields.Many2many('flota.impresora.tag', 'flota_impresora_impresora_tag_rel', 'impresora_tag_id', 'tag_id', 'Tags', copy=False)
    odometer = fields.Float(compute='_get_odometer', inverse='_set_odometer', string='Last Odometer',
        help='Odometer measure of the impresora at the moment of this log')
    odometer_unit = fields.Selection([
        ('kilometers', 'km'),
        ('miles', 'mi')
        ], 'Odometer Unit', default='kilometers', required=True)
    transmission = fields.Selection(
        [('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission',
        compute='_compute_model_fields', store=True, readonly=False)
    fuel_type = fields.Selection(FUEL_TYPES, 'Fuel Type', compute='_compute_model_fields', store=True, readonly=False)
    power_unit = fields.Selection([
        ('power', 'kW'),
        ('horsepower', 'Horsepower')
        ], 'Power Unit', default='power', required=True)
    horsepower = fields.Integer(compute='_compute_model_fields', store=True, readonly=False)
    horsepower_tax = fields.Float('Horsepower Taxation', compute='_compute_model_fields', store=True, readonly=False)
    power = fields.Integer('Power', help='Power in kW of the impresora', compute='_compute_model_fields', store=True, readonly=False)
    co2 = fields.Float('CO2 Emissions', help='CO2 emissions of the impresora', compute='_compute_model_fields', store=True, readonly=False, tracking=True, aggregator=None)
    co2_standard = fields.Char('CO2 Standard', compute='_compute_model_fields', store=True, readonly=False)
    category_id = fields.Many2one('flota.impresora.model.category', 'Category', compute='_compute_model_fields', store=True, readonly=False)
    image_128 = fields.Image(related='model_id.image_128', readonly=True)
    contract_renewal_due_soon = fields.Boolean(compute='_compute_contract_reminder', search='_search_contract_renewal_due_soon',
        string='Has Contracts to renew')
    contract_renewal_overdue = fields.Boolean(compute='_compute_contract_reminder', search='_search_get_overdue_contract_reminder',
        string='Has Contracts Overdue')
    contract_state = fields.Selection(
        [('futur', 'Incoming'),
         ('open', 'In Progress'),
         ('expired', 'Expired'),
         ('closed', 'Closed')
        ], string='Last Contract State', compute='_compute_contract_reminder', required=False)
    car_value = fields.Float(string="Catalog Value (VAT Incl.)")
    net_car_value = fields.Float(string="Purchase Value")
    residual_value = fields.Float()
    plan_to_change_car = fields.Boolean(related='driver_id.plan_to_change_car', store=True, readonly=False)
    plan_to_change_bike = fields.Boolean(related='driver_id.plan_to_change_bike', store=True, readonly=False)
    impresora_type = fields.Selection(related='model_id.impresora_type')
    frame_type = fields.Selection([('diamant', 'Diamant'), ('trapez', 'Trapez'), ('wave', 'Wave')], string="Bike Frame Type")
    electric_assistance = fields.Boolean(compute='_compute_model_fields', store=True, readonly=False)
    frame_size = fields.Float()
    service_activity = fields.Selection([
        ('none', 'None'),
        ('overdue', 'Overdue'),
        ('today', 'Today'),
    ], compute='_compute_service_activity')
    impresora_properties = fields.Properties('Properties', definition='model_id.impresora_properties_definition', copy=True)
    impresora_range = fields.Integer(string="Range")

    @api.depends('log_services')
    def _compute_service_activity(self):
        for impresora in self:
            activities_state = set(state for state in impresora.log_services.mapped('activity_state') if state and state != 'planned')
            impresora.service_activity = sorted(activities_state)[0] if activities_state else 'none'

    @api.depends('model_id')
    def _compute_model_fields(self):
        '''
        Copies all the related fields from the model to the impresora
        '''
        model_values = dict()
        for impresora in self.filtered('model_id'):
            if impresora.model_id.id in model_values:
                write_vals = model_values[impresora.model_id.id]
            else:
                # copy if value is truthy
                write_vals = {MODEL_FIELDS_TO_VEHICLE[key]: impresora.model_id[key] for key in MODEL_FIELDS_TO_VEHICLE\
                    if impresora.model_id[key]}
                model_values[impresora.model_id.id] = write_vals
            impresora.update(write_vals)

    @api.depends('model_id.brand_id.name', 'model_id.name', 'license_plate')
    def _compute_impresora_name(self):
        for record in self:
            record.name = (record.model_id.brand_id.name or '') + '/' + (record.model_id.name or '') + '/' + (record.license_plate or _('No Plate'))

    def _get_odometer(self):
        FlotaVehicalOdometer = self.env['flota.impresora.odometer']
        for record in self:
            impresora_odometer = FlotaVehicalOdometer.search([('impresora_id', '=', record.id)], limit=1, order='value desc')
            if impresora_odometer:
                record.odometer = impresora_odometer.value
            else:
                record.odometer = 0

    def _set_odometer(self):
        for record in self:
            if record.odometer:
                date = fields.Date.context_today(record)
                data = {'value': record.odometer, 'date': date, 'impresora_id': record.id}
                self.env['flota.impresora.odometer'].create(data)

    def _compute_count_all(self):
        Odometer = self.env['flota.impresora.odometer']
        LogService = self.env['flota.impresora.log.services'].with_context(active_test=False)
        LogContract = self.env['flota.impresora.log.contract'].with_context(active_test=False)
        History = self.env['flota.impresora.assignation.log']
        odometers_data = Odometer._read_group([('impresora_id', 'in', self.ids)], ['impresora_id'], ['__count'])
        services_data = LogService._read_group([('impresora_id', 'in', self.ids)], ['impresora_id', 'active'], ['__count'])
        logs_data = LogContract._read_group([('impresora_id', 'in', self.ids), ('state', '!=', 'closed')], ['impresora_id', 'active'], ['__count'])
        histories_data = History._read_group([('impresora_id', 'in', self.ids)], ['impresora_id'], ['__count'])

        mapped_odometer_data = defaultdict(lambda: 0)
        mapped_service_data = defaultdict(lambda: defaultdict(lambda: 0))
        mapped_log_data = defaultdict(lambda: defaultdict(lambda: 0))
        mapped_history_data = defaultdict(lambda: 0)

        for impresora, count in odometers_data:
            mapped_odometer_data[impresora.id] = count
        for impresora, active, count in services_data:
            mapped_service_data[impresora.id][active] = count
        for impresora, active, count in logs_data:
            mapped_log_data[impresora.id][active] = count
        for impresora, count in histories_data:
            mapped_history_data[impresora.id] = count

        for impresora in self:
            impresora.odometer_count = mapped_odometer_data[impresora.id]
            impresora.service_count = mapped_service_data[impresora.id][impresora.active]
            impresora.contract_count = mapped_log_data[impresora.id][impresora.active]
            impresora.history_count = mapped_history_data[impresora.id]

    @api.depends('log_contracts')
    def _compute_contract_reminder(self):
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('hr_flota.delay_alert_contract', default=30))
        current_date = fields.Date.context_today(self)
        data = self.env['flota.impresora.log.contract']._read_group(
            domain=[('expiration_date', '!=', False), ('impresora_id', 'in', self.ids), ('state', '!=', 'closed')],
            groupby=['impresora_id', 'state'],
            aggregates=['expiration_date:max'])

        prepared_data = {}
        for impresora_id, state, expiration_date in data:
            if prepared_data.get(impresora_id.id):
                if prepared_data[impresora_id.id]['expiration_date'] < expiration_date:
                    prepared_data[impresora_id.id]['expiration_date'] = expiration_date
                    prepared_data[impresora_id.id]['state'] = state
            else:
                prepared_data[impresora_id.id] = {
                    'state': state,
                    'expiration_date': expiration_date,
                }

        for record in self:
            impresora_data = prepared_data.get(record.id)
            if impresora_data:
                diff_time = (impresora_data['expiration_date'] - current_date).days
                record.contract_renewal_overdue = diff_time < 0
                record.contract_renewal_due_soon = not record.contract_renewal_overdue and (diff_time < delay_alert_contract)
                record.contract_state = impresora_data['state']
            else:
                record.contract_renewal_overdue = False
                record.contract_renewal_due_soon = False
                record.contract_state = ""

    def _get_analytic_name(self):
        # This function is used in flota_account and is overrided in l10n_be_hr_payroll_flota
        return self.license_plate or _('No plate')

    def _search_contract_renewal_due_soon(self, operator, value):
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('hr_flota.delay_alert_contract', default=30))
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        datetime_today = fields.Datetime.from_string(today)
        limit_date = fields.Datetime.to_string(datetime_today + relativedelta(days=+delay_alert_contract))
        res_ids = self.env['flota.impresora.log.contract'].search([
            ('expiration_date', '>', today),
            ('expiration_date', '<', limit_date),
            ('state', 'in', ['open', 'expired'])
        ]).mapped('impresora_id').ids
        res.append(('id', search_operator, res_ids))
        return res

    def _search_get_overdue_contract_reminder(self, operator, value):
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        # get the id of impresoras that have overdue contracts
        # but exclude those for which a new contract has already been created for them
        impresora_ids = self.env['flota.impresora']._search([
            ("log_contracts", "any", [
                ('expiration_date', '!=', False),
                ('expiration_date', '<', today),
                ('state', 'in', ['open', 'expired'])
            ]),
            "!",
                ("log_contracts", "any", [
                    ('expiration_date', '!=', False),
                    ('expiration_date', '>=', today),
                    ('state', 'in', ['open', 'futur'])
                ]),
        ])
        res.append(('id', search_operator, impresora_ids))
        return res

    def _clean_vals_internal_user(self, vals):
        # Flota administrator may not have rights to write on partner
        # related fields when the driver_id is a res.user.
        # This trick is used to prevent access right error.
        su_vals = {}
        if self.env.su:
            return su_vals
        if 'plan_to_change_car' in vals:
            su_vals['plan_to_change_car'] = vals.pop('plan_to_change_car')
        if 'plan_to_change_bike' in vals:
            su_vals['plan_to_change_bike'] = vals.pop('plan_to_change_bike')
        return su_vals

    @api.model_create_multi
    def create(self, vals_list):
        ptc_values = [self._clean_vals_internal_user(vals) for vals in vals_list]
        impresoras = super().create(vals_list)
        for impresora, vals, ptc_value in zip(impresoras, vals_list, ptc_values):
            if ptc_value:
                impresora.sudo().write(ptc_value)
            if 'driver_id' in vals and vals['driver_id']:
                impresora.create_driver_history(vals)
            if 'future_driver_id' in vals and vals['future_driver_id']:
                state_waiting_list = self.env.ref('flota.flota_impresora_state_waiting_list', raise_if_not_found=False)
                states = impresora.mapped('state_id').ids
                if not state_waiting_list or state_waiting_list.id not in states:
                    future_driver = self.env['res.partner'].browse(vals['future_driver_id'])
                    if self.impresora_type == 'bike':
                        future_driver.sudo().write({'plan_to_change_bike': True})
                    if self.impresora_type == 'car':
                        future_driver.sudo().write({'plan_to_change_car': True})
        return impresoras

    def write(self, vals):
        if 'odometer' in vals and any(impresora.odometer > vals['odometer'] for impresora in self):
            raise UserError(_('The odometer value cannot be lower than the previous one.'))

        if 'driver_id' in vals and vals['driver_id']:
            driver_id = vals['driver_id']
            for impresora in self.filtered(lambda v: v.driver_id.id != driver_id):
                impresora.create_driver_history(vals)
                if impresora.driver_id:
                    impresora.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=impresora.manager_id.id or self.env.user.id,
                        note=_('Specify the End date of %s', impresora.driver_id.name))

        if 'future_driver_id' in vals and vals['future_driver_id']:
            state_waiting_list = self.env.ref('flota.flota_impresora_state_waiting_list', raise_if_not_found=False)
            states = self.mapped('state_id').ids if 'state_id' not in vals else [vals['state_id']]
            if not state_waiting_list or state_waiting_list.id not in states:
                future_driver = self.env['res.partner'].browse(vals['future_driver_id'])
                if self.impresora_type == 'bike':
                    future_driver.sudo().write({'plan_to_change_bike': True})
                if self.impresora_type == 'car':
                    future_driver.sudo().write({'plan_to_change_car': True})

        if 'active' in vals and not vals['active']:
            self.env['flota.impresora.log.contract'].search([('impresora_id', 'in', self.ids)]).active = False
            self.env['flota.impresora.log.services'].search([('impresora_id', 'in', self.ids)]).active = False

        su_vals = self._clean_vals_internal_user(vals)
        if su_vals:
            self.sudo().write(su_vals)
        res = super(FlotaImpresora, self).write(vals)
        return res

    def _get_driver_history_data(self, vals):
        self.ensure_one()
        return {
            'impresora_id': self.id,
            'driver_id': vals['driver_id'],
            'date_start': fields.Date.today(),
        }

    def create_driver_history(self, vals):
        for impresora in self:
            self.env['flota.impresora.assignation.log'].create(
                impresora._get_driver_history_data(vals),
            )

    def action_accept_driver_change(self):
        # Find all the impresoras of the same type for which the driver is the future_driver_id
        # remove their driver_id and close their history using current date
        impresoras = self.search([('driver_id', 'in', self.mapped('future_driver_id').ids), ('impresora_type', '=', self.impresora_type)])
        impresoras.write({'driver_id': False})

        for impresora in self:
            if impresora.impresora_type == 'bike':
                impresora.future_driver_id.sudo().write({'plan_to_change_bike': False})
            if impresora.impresora_type == 'car':
                impresora.future_driver_id.sudo().write({'plan_to_change_car': False})
            impresora.driver_id = impresora.future_driver_id
            impresora.future_driver_id = False

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current impresora """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:

            res = self.env['ir.actions.act_window']._for_xml_id('flota.%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_impresora_id=self.id, group_by=False),
                domain=[('impresora_id', '=', self.id)]
            )
            return res
        return False

    def act_show_log_cost(self):
        """ This opens log view to view and add new log for this impresora, groupby default to only show effective costs
            @return: the costs log view
        """
        self.ensure_one()
        copy_context = dict(self.env.context)
        copy_context.pop('group_by', None)
        res = self.env['ir.actions.act_window']._for_xml_id('flota.flota_impresora_costs_action')
        res.update(
            context=dict(copy_context, default_impresora_id=self.id, search_default_parent_false=True),
            domain=[('impresora_id', '=', self.id)]
        )
        return res

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'driver_id' in init_values or 'future_driver_id' in init_values:
            return self.env.ref('flota.mt_flota_driver_updated')
        return super(FlotaImpresora, self)._track_subtype(init_values)

    def open_assignation_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assignment Logs',
            'view_mode': 'list',
            'res_model': 'flota.impresora.assignation.log',
            'domain': [('impresora_id', '=', self.id)],
            'context': {'default_driver_id': self.driver_id.id, 'default_impresora_id': self.id}
        }

    def action_send_email(self):
        return {
            'name': _('Send Email'),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'flota.impresora.send.mail',
            'context': {
                'default_impresora_ids': self.ids,
            }
        }
