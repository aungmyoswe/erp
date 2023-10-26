{
    'name':
    'Cashbook',
    'version':
    '1.1.0',
    'category':
    'account',
    'summary':
    'Cashbook Customization',
    'description':
    """
This module is Cashbook customization.
    """,
    'depends': ['base', 'account', 'account_invoicing'],
    'data': [
        'security/ir.model.access.csv',
        'views/cashbook_view.xml',
        'views/res_config_setting_view.xml',
    ],
    'installable':
    True,
    'auto_install':
    False,
}
