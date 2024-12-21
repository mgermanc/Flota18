# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class FlotaImpresoraState(models.Model):
    _name = 'flota.impresora.state'
    _order = 'sequence asc'
    _description = 'Impresora Status'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()

    _sql_constraints = [('flota_state_name_unique', 'unique(name)', 'State name already exists')]
