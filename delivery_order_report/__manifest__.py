{
    'name': 'Delivery Order Report',
    'version': '1.0',
    'category': 'Inventory',
    'sequence': 20,
    'summary': 'Delivery Order Report',
    'description': "",
    'depends': ['base','stock'],
    'data': [
        'views/delivery_order_view.xml',
        'security/ir.model.access.csv'
    ],

    'installable': True,
    'application': True,
    
}
