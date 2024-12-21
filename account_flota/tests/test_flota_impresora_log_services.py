# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

@tagged('post_install', '-at_install')
class TestFlotaImpresoraLogServices(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({'name': "Vendor"})
        cls.purchaser = cls.env['res.partner'].create({'name': "Purchaser"})
        brand = cls.env["flota.impresora.model.brand"].create({
            "name": "Audi",
        })
        model = cls.env["flota.impresora.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        cls.car_1, cls.car_2 = cls.env["flota.impresora"].create([
            {
                "model_id": model.id,
                "driver_id": cls.purchaser.id,
                "plan_to_change_car": False
            },
            {
                "model_id": model.id,
                "driver_id": cls.purchaser.id,
                "plan_to_change_car": False
            }
        ])
        cls.bill = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.vendor.id,
            'invoice_date': '2019-01-01',
            'date': '2019-01-01',
        })
        cls.service_line = cls.env['account.move.line'].create({
            'name': 'line',
            'price_unit': 50.0,
            'impresora_id': cls.car_1.id,
            'move_id': cls.bill.id,
        })
        cls.flota_service_type = cls.env['flota.service.type'].create({
            'name': 'Test service type',
            'category': 'service',
        })

    def test_service_bill_right_amount(self):
        self.bill.action_post()

        # check if the log service is created
        self.assertEqual(self.car_1.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_1.log_services[0].amount, self.service_line.price_subtotal)

        self.bill.button_draft()
        self.service_line.price_unit = 110
        self.bill.action_post()

        # check if the log service's amount is equal to the new price
        self.assertEqual(self.car_1.log_services[0].amount, self.service_line.price_unit)

    def test_service_bill_deletion(self):
        service_line_2 = self.env['account.move.line'].create({
            'name': 'line',
            'price_unit': 150.0,
            'impresora_id': self.car_2.id,
            'move_id': self.bill.id,
        })

        self.bill.action_post()

        # check if the log service is created
        self.assertEqual(self.car_1.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_1.log_services[0].amount, self.service_line.price_subtotal)
        self.assertEqual(self.car_2.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_2.log_services[0].amount, service_line_2.price_subtotal)

        self.bill.button_draft()
        self.service_line.unlink()

        self.assertFalse(self.car_1.log_services)
        self.assertEqual(self.car_2.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_2.log_services[0].amount, service_line_2.price_subtotal)

    def test_service_log_deletion(self):
        self.bill.action_post()

        # check if the log service is created
        self.assertEqual(self.car_1.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_1.log_services[0].amount, self.service_line.price_subtotal)

        # a log services linked to a bill cannot be deleted
        with self.assertRaises(UserError):
            self.car_1.log_services[0].unlink()

        log_service_without_bill = self.env['flota.impresora.log.services'].create({
            'impresora_id': self.car_1.id,
            'service_type_id': self.flota_service_type.id,
            'amount': 1440,
        })

        log_service_without_bill.unlink()

    def test_service_bill_change_impresora(self):
        self.bill.action_post()

        # check if the log service is created
        self.assertEqual(self.car_1.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_1.log_services[0].amount, self.service_line.price_subtotal)

        self.bill.button_draft()
        self.service_line.impresora_id = self.car_2
        self.bill.action_post()

        self.assertFalse(self.car_1.log_services)
        self.assertEqual(self.car_2.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_2.log_services[0].amount, self.service_line.price_subtotal)

        # remove the impresora should also delete the service
        self.bill.button_draft()
        self.service_line.impresora_id = False
        self.bill.action_post()

        self.assertFalse(self.car_2.log_services)
        self.assertFalse(self.service_line.impresora_log_service_ids)

        # putting car 2 back should create a new service
        self.bill.button_draft()
        self.service_line.impresora_id = self.car_2
        self.bill.action_post()

        self.assertEqual(self.car_2.log_services[0].account_move_line_id.move_id, self.bill)
        self.assertEqual(self.car_2.log_services[0].amount, self.service_line.price_subtotal)

    def test_flota_log_services_amount(self):
        other_currency = self.setup_other_currency('EUR')
        brand = self.env["flota.impresora.model.brand"].create({
            "name": "Audi",
        })
        model = self.env["flota.impresora.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        car = self.env["flota.impresora"].create({
            "model_id": model.id,
            "plan_to_change_car": False
        })

        partner = self.env['res.partner'].create({
            "name": "Test Partner",
        })

        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': partner.id,
            'invoice_date': '2019-01-01',
            'date': '2019-01-01',
            'currency_id': other_currency.id,
            'line_ids': [
                (0, 0, {
                    'account_id': self.company_data['default_account_expense'].id,
                    'impresora_id': car.id,
                    'quantity': 1,
                    'price_unit': 5000
                })
            ],
        })
        move.action_post()
        line = move.line_ids[0]
        flota_service = self.env['flota.impresora.log.services'].search([('vendor_id', '=', partner.id),
                                                                       ('description', '=', False)])

        self.assertNotEqual(line.debit, line.price_subtotal)
        self.assertEqual(flota_service.amount, line.debit)
