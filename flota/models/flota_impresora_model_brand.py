# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FlotaImpresoraModelBrand(models.Model):
    _name = 'flota.impresora.model.brand'
    _description = 'Brand of the impresora'
    _order = 'name asc'

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True)
    image_128 = fields.Image("Logo", max_width=128, max_height=128)
    model_count = fields.Integer(compute="_compute_model_count", string="", store=True)
    model_ids = fields.One2many('flota.impresora.model', 'brand_id')

    @api.depends('model_ids')
    def _compute_model_count(self):
        model_data = self.env['flota.impresora.model']._read_group([
            ('brand_id', 'in', self.ids),
        ], ['brand_id'], ['__count'])
        models_brand = {brand.id: count for brand, count in model_data}

        for record in self:
            record.model_count = models_brand.get(record.id, 0)

    def action_brand_model(self):
        self.ensure_one()
        view = {
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'flota.impresora.model',
            'name': 'Models',
            'context': {'search_default_brand_id': self.id, 'default_brand_id': self.id}
        }

        return view
