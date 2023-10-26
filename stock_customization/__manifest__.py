# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Stock Customization',
    'version': '1.0',
    'category': 'Inventory',
    'sequence': 20,
    'summary': 'Stock Customization',
    'description': "",
    'depends': ['stock','web'],
    'data': [
        'views/stock_view.xml',
        'report/report_deliveryslip.xml',
        'report/report_templates.xml',
        'report/stock_report_views.xml',
    ],

    'installable': True,
    'application': True,
    
}
