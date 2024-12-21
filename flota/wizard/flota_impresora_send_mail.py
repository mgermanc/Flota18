# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class FlotaImpresoraSendMail(models.TransientModel):
    _name = 'flota.impresora.send.mail'
    _inherit = 'mail.composer.mixin'
    _description = 'Send mails to Drivers'

    impresora_ids = fields.Many2many('flota.impresora', string='Impresoras', required=True)
    author_id = fields.Many2one('res.partner', 'Author', required=True, default=lambda self: self.env.user.partner_id.id)
    template_id = fields.Many2one(domain=lambda self: [('model_id', '=', self.env['ir.model']._get('flota.impresora').id)])
    attachment_ids = fields.Many2many(
        'ir.attachment', 'flota_impresora_mail_compose_message_ir_attachments_rel',
        'wizard_id', 'attachment_id', string='Attachments')

    @api.onchange('template_id')
    def _onchange_template_id(self):
        self.attachment_ids = self.template_id.attachment_ids

    def action_send(self):
        self.ensure_one()
        without_emails = self.impresora_ids.driver_id.filtered(lambda a: not a.email)
        if without_emails:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': _("The following impresora drivers are missing an email address: %s.", ', '.join(without_emails.mapped("name"))),
                }
            }

        for impresora in self.impresora_ids:
            impresora.message_post(
                author_id=self.author_id.id,
                body=self.body,
                email_layout_xmlid='mail.mail_notification_light',
                message_type='comment',
                partner_ids=impresora.driver_id.ids,
                subject=self.subject,
            )

    def action_save_as_template(self):
        model = self.env['ir.model']._get('flota.impresora')
        template_name = _("Impresora: Mass mail drivers")
        template = self.env['mail.template'].create({
            'name': template_name,
            'subject': self.subject or False,
            'body_html': self.body or False,
            'model_id': model.id,
            'use_default_to': True,
        })

        if self.attachment_ids:
            attachments = self.env['ir.attachment'].sudo().browse(self.attachment_ids.ids).filtered(lambda a: a.create_uid.id == self._uid)
            if attachments:
                attachments.write({'res_model': template._name, 'res_id': template.id})
            template.attachment_ids |= self.attachment_ids

        self.write({'template_id': template.id})

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': template.id,
            'res_model': 'mail.template',
            'target': 'new',
        }
