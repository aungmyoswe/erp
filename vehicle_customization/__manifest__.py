{
    'name':
    'Vehicle Customization',
    'version':
    '1.1',
    'category':
    'Inventory',
    'sequence':
    20,
    'summary':
    'Vehicle Customization',
    'description':
    "",
    'depends': ['base', 'web', 'stock', 'stock_customization'],
    'data': [
        'views/car_view.xml',
        'views/driver_view.xml',
        'views/vehicle_invoice_view.xml',
        'views/report_vehicle.xml',
        'security/ir.model.access.csv',
        'views/report_templates.xml',
        'views/vehicle_report.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable':
    True,
    'application':
    True,
}
