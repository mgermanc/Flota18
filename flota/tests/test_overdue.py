# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tests import common, new_test_user
from odoo import fields


class TestFlota(common.TransactionCase):

    def test_search_renewal(self):
        """
            Should find the car with overdue contract or renewal due soon
        """
        user = new_test_user(self.env, "test base user", groups="base.group_user")
        brand = self.env["flota.impresora.model.brand"].create({
            "name": "Audi",
        })
        model = self.env["flota.impresora.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        car_1 = self.env["flota.impresora"].create({
            "model_id": model.id,
            "driver_id": user.partner_id.id,
            "plan_to_change_car": False
        })

        car_2 = self.env["flota.impresora"].create({
            "model_id": model.id,
            "driver_id": user.partner_id.id,
            "plan_to_change_car": False
        })
        Log = self.env['flota.impresora.log.contract']
        Log.create({
            'impresora_id': car_2.id,
            'expiration_date': fields.Date.add(fields.Date.today(), days=10)
        })
        res = self.env["flota.impresora"].search([('contract_renewal_due_soon', '=', True), ('id', '=', car_2.id)])
        self.assertEqual(res, car_2)

        Log.create({
            'impresora_id': car_1.id,
            'expiration_date': fields.Date.add(fields.Date.today(), days=-10)
        })
        res = self.env["flota.impresora"].search([('contract_renewal_overdue', '=', True), ('id', '=', car_1.id)])
        self.assertEqual(res, car_1)

    def test_exclude_resolved_impresoras_from_overdue(self):
        """
            if there is an expired contract for the car, but it also has an open contract
            it should not be considered overdue
        """
        user = new_test_user(self.env, "test base user", groups="base.group_user")
        brand = self.env["flota.impresora.model.brand"].create({
            "name": "Audi",
        })
        model = self.env["flota.impresora.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        car_1 = self.env["flota.impresora"].create({
            "model_id": model.id,
            "driver_id": user.partner_id.id,
            "plan_to_change_car": False
        })

        Log = self.env['flota.impresora.log.contract']
        Log.create({
            'impresora_id': car_1.id,
            'expiration_date': fields.Date.add(fields.Date.today(), days=-2)
        })
        Log.create({
            'impresora_id': car_1.id,
            'expiration_date': fields.Date.add(fields.Date.today(), days=365)
        })

        res = self.env["flota.impresora"].search([('contract_renewal_overdue', '=', True), ('id', '=', car_1.id)])
        self.assertFalse(res)
