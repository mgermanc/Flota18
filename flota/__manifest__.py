# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Flota',
    'version' : '0.1',
    'sequence': 185,
    'category': 'Human Resources/Flota',
    'website' : 'https://www.odoo.com/app/flota',
    'summary' : 'Manage your flota and track car costs',
    'description' : """
Impresora, leasing, insurances, cost
==================================
With this module, Odoo helps you managing all your impresoras, the
contracts associated to those impresora as well as services, costs
and many other features necessary to the management of your flota
of impresora(s)

Main Features
-------------
* Add impresoras to your flota
* Manage contracts for impresoras
* Reminder when a contract reach its expiration date
* Add services, odometer values for all impresoras
* Show all costs associated to a impresora or to a type of service
* Analysis graph for costs
""",
    'depends': [
        'base',
        'mail',
        'maintenance',
        'repair'
    ],
    'data': [
        'security/flota_security.xml',
        'security/ir.model.access.csv',
        'views/flota_impresora_model_views.xml',
        'views/flota_impresora_views.xml',
        'views/flota_impresora_cost_views.xml',
        'views/flota_board_view.xml',
        'views/mail_activity_views.xml',
        'views/res_config_settings_views.xml',
        'views/flota_man_rep_views.xml',
        'views/flota_man_rep_inherit_views.xml',
        'data/flota_cars_data.xml',
        'data/flota_data.xml',
        'data/mail_message_subtype_data.xml',
        'data/mail_activity_type_data.xml',
        'wizard/flota_impresora_send_mail_views.xml'
    ],

    'demo': ['data/flota_demo.xml'],

    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'flota/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
}
