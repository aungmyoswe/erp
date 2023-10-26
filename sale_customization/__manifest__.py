{
    'name': 'Sale Customization',
    'version': '1.1',
    'category': 'Sale',
    'summary': 'Sales Customization',
    'description': """
This module is Sales customization.
    """,
    'depends': ['sale','stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'uninstall_hook': "uninstall_hook",
    'installable': True,
    'auto_install': False,
}
