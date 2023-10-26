# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name':
    'FOC Customization',
    'version':
    '1.2',
    'category':
    'Inventory',
    'summary':
    'FOC Customization',
    'author':
    'Aung Myo Swe',
    'mail':
    'aungmyoswe.dev@gmail.com',
    'description':
    "",
    'depends': [
        'stock',
        'product_uom_multis',
        'vehicle_customization',
        'stock_customization',
        'product_valutation_report',
        'sale_customization',
        'delivery_order_report',
    ],
    'data': [
        'views/stock_move_view.xml',
        'views/product_valuation_view.xml',
        'report/report_vehicle.xml',
        'report/delivery_template_report.xml',
    ],
    'installable':
    True,
    'application':
    True,
}
