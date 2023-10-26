{
    'name':
    'Branch Customization',
    'version':
    '1.2',
    'category':
    'Branch',
    'summary':
    'Branch for sales, purchase and invoice',
    'description':
    """
This module is branch customization for sale, customer invoice, purchase , vendor bill and payment.
    """,
    'depends': ['base', 'sale_management', 'purchase', 'account'],
    'data': [
        'views/sale_views.xml',
        'views/account_invoice_view.xml',
        #'views/account_voucher_views.xml',
        'views/res_branch_view.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/purchase_views.xml',
        'views/account_report.xml',
        'views/report_invoice.xml',
        'views/report_templates.xml',
        'views/account_payment_view.xml',
        'views/stock_picking_views.xml',
    ],
    'uninstall_hook':
    "uninstall_hook",
    'installable':
    True,
    'auto_install':
    False,
}
