# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FlotaImpresoraLogServices(models.Model):
    _name = 'flota.impresora.log.services'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'service_type_id'
    _description = 'Services for impresoras'

    active = fields.Boolean(default=True)
    impresora_id = fields.Many2one('flota.impresora', 'Impresora', required=True)
    manager_id = fields.Many2one('res.users', 'Flota Manager', related='impresora_id.manager_id', store=True)
    amount = fields.Monetary('Cost')
    description = fields.Char('Description')
    odometer_id = fields.Many2one('flota.impresora.odometer', 'Odometer', help='Odometer measure of the impresora at the moment of this log')
    odometer = fields.Float(
        compute="_get_odometer", inverse='_set_odometer', string='Odometer Value',
        help='Odometer measure of the impresora at the moment of this log')
    odometer_unit = fields.Selection(related='impresora_id.odometer_unit', string="Unit", readonly=True)
    date = fields.Date(help='Date when the cost has been executed', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    purchaser_id = fields.Many2one('res.partner', string="Driver", compute='_compute_purchaser_id', readonly=False, store=True)
    inv_ref = fields.Char('Vendor Reference')
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    notes = fields.Text()
    repair_order_id = fields.Many2one('repair.order', string='Orden de Repacion')
    service_type_id = fields.Many2one(
        'flota.service.type', 'Service Type', required=True,
        default=lambda self: self.env.ref('flota.type_service_service_7', raise_if_not_found=False),
    )
    state = fields.Selection([
        ('new', 'New'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='new', string='Stage', group_expand=True, tracking=True)


    def _get_odometer(self):
        self.odometer = 0
        for record in self:
            if record.odometer_id:
                record.odometer = record.odometer_id.value

    def _set_odometer(self):
        for record in self:
            if not record.odometer:
                raise UserError(_('Emptying the odometer value of a impresora is not allowed.'))
            odometer = self.env['flota.impresora.odometer'].create({
                'value': record.odometer,
                'date': record.date or fields.Date.context_today(record),
                'impresora_id': record.impresora_id.id
            })
            self.odometer_id = odometer

    @api.model_create_multi
    def create(self, vals_list):
        for data in vals_list:
            if 'odometer' in data and not data['odometer']:
                # if received value for odometer is 0, then remove it from the
                # data as it would result to the creation of a
                # odometer log with 0, which is to be avoided
                del data['odometer']
        return super(FlotaImpresoraLogServices, self).create(vals_list)

    @api.depends('impresora_id')
    def _compute_purchaser_id(self):
        for service in self:
            service.purchaser_id = service.impresora_id.driver_id