# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FlotaImpresoraOdometer(models.Model):
    _name = 'flota.impresora.odometer'
    _description = 'Odometer log for a impresora'
    _order = 'date desc'

    name = fields.Char(compute='_compute_impresora_log_name', store=True)
    date = fields.Date(default=fields.Date.context_today)
    value = fields.Float('Odometer Value', aggregator="max")
    impresora_id = fields.Many2one('flota.impresora', 'Impresora', required=True)
    unit = fields.Selection(related='impresora_id.odometer_unit', string="Unit", readonly=True)
    driver_id = fields.Many2one(related="impresora_id.driver_id", string="Driver", readonly=False)

    @api.depends('impresora_id', 'date')
    def _compute_impresora_log_name(self):
        for record in self:
            name = record.impresora_id.name
            if not name:
                name = str(record.date)
            elif record.date:
                name += ' / ' + str(record.date)
            record.name = name

    @api.onchange('impresora_id')
    def _onchange_impresora(self):
        if self.impresora_id:
            self.unit = self.impresora_id.odometer_unit
