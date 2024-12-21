# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, models, fields


class FlotaImpresora(models.Model):
    _inherit = 'flota.impresora'

    bill_count = fields.Integer(compute='_compute_move_ids', string="Bills Count")
    account_move_ids = fields.One2many('account.move', compute='_compute_move_ids')

    def _compute_move_ids(self):
        if not self.env.user.has_group('account.group_account_readonly'):
            self.account_move_ids = False
            self.bill_count = 0
            return

        moves = self.env['account.move.line']._read_group(
            domain=[
                ('impresora_id', 'in', self.ids),
                ('parent_state', '!=', 'cancel'),
                ('move_id.move_type', 'in', self.env['account.move'].get_purchase_types())
            ],
            groupby=['impresora_id'],
            aggregates=['move_id:array_agg'],
        )
        impresora_move_mapping = {impresora.id: set(move_ids) for impresora, move_ids in moves}
        for impresora in self:
            impresora.account_move_ids = [Command.set(impresora_move_mapping.get(impresora.id, []))]
            impresora.bill_count = len(impresora.account_move_ids)

    def action_view_bills(self):
        self.ensure_one()

        form_view_ref = self.env.ref('account.view_move_form', False)
        list_view_ref = self.env.ref('account_flota.account_move_view_tree', False)

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        result.update({
            'domain': [('id', 'in', self.account_move_ids.ids)],
            'views': [(list_view_ref.id, 'list'), (form_view_ref.id, 'form')],
        })
        return result
