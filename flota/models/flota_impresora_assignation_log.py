# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FlotaImpresoraAssignationLog(models.Model):
    _name = "flota.impresora.assignation.log"
    _description = "Drivers history on a impresora"
    _order = "create_date desc, date_start desc"

    impresora_id = fields.Many2one('flota.impresora', string="Impresora", required=True)
    driver_id = fields.Many2one('res.partner', string="Driver", required=True)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")

    @api.depends('driver_id', 'impresora_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.impresora_id.name} - {rec.driver_id.name}'
