from odoo import models, fields


class FlotaManRep(models.Model):
    _name = 'flota.man.rep'
    _description = 'Administración de Impresoras'
    _order = 'name desc'
    name = fields.Char(string='Nombre', required=True)
    maintenance_id = fields.Many2one('maintenance.equipment', string='Equipo')
    impresora_id = fields.Many2one('flota.impresora', string='Impresora')
    product_id = fields.Many2one('product.product', string='Producto')
    partner_id = fields.Many2one('res.partner', string='Cliente')
