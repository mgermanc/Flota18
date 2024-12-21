# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tests import common, new_test_user


class TestFlota(common.TransactionCase):

    def test_manager_create_impresora(self):
        manager = new_test_user(self.env, "test flota manager", groups="flota.flota_group_manager,base.group_partner_manager")
        user = new_test_user(self.env, "test base user", groups="base.group_user")
        brand = self.env["flota.impresora.model.brand"].create({
            "name": "Audi",
        })
        model = self.env["flota.impresora.model"].create({
            "brand_id": brand.id,
            "name": "A3",
        })
        car = self.env["flota.impresora"].with_user(manager).create({
            "model_id": model.id,
            "driver_id": user.partner_id.id,
            "plan_to_change_car": False
        })
        car.with_user(manager).plan_to_change_car = True
