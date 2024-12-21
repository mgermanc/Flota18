from pkg_resources import require

from odoo import api, models, fields


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    printeradmin_id = fields.Many2one('flota.man.rep', string='Impresora Administrada')
    repair_id = fields.Many2one('repair.order', string='Repair Order')
    partner_id = fields.Many2one('res.partner', string='Cliente')

    @api.onchange('printeradmin_id')
    def _onchange_printeradmin(self):
        if self.printeradmin_id:
            self.equipment_id = self.printeradmin_id.maintenance_id
            self.partner_id = self.printeradmin_id.partner_id


    def action_create_repair_order(self):
        self.ensure_one()
        if not self.repair_id:
            self.partner_id = self.printeradmin_id.partner_id.id
            repair_order = self.env['repair.order'].create({
            'printeradmin_id': self.printeradmin_id.id,
            'product_id': self.printeradmin_id.product_id.id,
            'partner_id': self.partner_id.id,
            'maintenance_id': self.id })


            return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Reparación',
            'view_mode': 'form',
            'res_model': 'repair.order',
            'res_id': repair_order.id,
            'target': 'current',
            }
        else:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Reparación',
            'view_mode': 'form',
            'res_model': 'repair.order',
            'res_id': self.repair_id.id,
            'target': 'current',
        }


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    printeradmin_id = fields.Many2one('flota.man.rep', string='Impresora Administrada')
    maintenance_id = fields.Many2one('maintenance.request', string='Pedido de mantenimiento')
    log_service_id = fields.Many2one('flota.impresora.log.services', string ='Log Services')
    flota_service_type_id = fields.Many2one('flota.service.type',string='Tipo de Servicio', required=True)

    def action_validate(self):
        self.ensure_one(),
        res = super(RepairOrder, self).action_validate()
        for order in self:
            if order.maintenance_id:
                maintenance_request = order.maintenance_id
                maintenance_request.write({'kanban_state': 'done', 'repair_id': order.id})
            if not order.sale_order_id:
                order.action_create_sale_order()
        return res

    def action_create_sale_order(self):
        self.ensure_one(),
        res = super(RepairOrder, self).action_create_sale_order()
        return res


    def action_repair_end(self):
        self.ensure_one(),
        res = super(RepairOrder, self).action_repair_end()
        if self.sale_order_id.id:
            costo = self.sale_order_id.amount_total
        else: costo = 0.00
        if self.maintenance_id.id:
            self.maintenance_id.write({'stage_id': 3})


        if not self.log_service_id:
            self.partner_id = self.printeradmin_id.partner_id.id
            log_service = self.env['flota.impresora.log.services'].create({
            'printeradmin_id': self.printeradmin_id.id,
            'impresora_id': self.printeradmin_id.impresora_id.id,
            'vendor_id': self.partner_id.id,
            'repair_order_id': self.id,
            'amount': costo,
            'service_type_id': self.flota_service_type_id.id,
            'description':self.maintenance_id.name})

            if log_service:
                self.log_service_id = log_service.id
            return {
            'type': 'ir.actions.act_window',
            'name': 'Log de Servicios',
            'view_mode': 'form',
            'res_model': 'flota.impresora.log.service',
            'res_id': log_service.id,
            'target': 'current',
            }
        else:
            return {
            'type': 'ir.actions.act_window',
            'name': 'Log de Servicio',
            'view_mode': 'form',
            'res_model': 'flota.impresora.log.service',
            'res_id': self.log_service_id.id,
            'target': 'current',
        }



        return res





class FlotaImpresoraLogServices(models.Model):
    _inherit = 'flota.impresora.log.services'

    printeradmin_id = fields.Many2one('flota.man.rep', string='Impresora Administrada')


