# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Accounting/Flota bridge',
    'category': 'Accounting/Accounting',
    'summary': 'Manage accounting with flotas',
    'version': '1.0',
    'depends': ['flota', 'account'],
    'data': [
        'data/flota_service_type_data.xml',
        'views/account_move_views.xml',
        'views/flota_impresora_views.xml',
        'views/flota_impresora_log_services_views.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
}
