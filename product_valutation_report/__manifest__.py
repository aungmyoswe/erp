# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name':
    'Product Valuation Reports',
    'version':
    '0.1.2',
    'category':
    'Inventory',
    'summary':
    "Product Valuation Report",
    'author':
    'Aung Myo Swe',
    'license':
    'AGPL-3',
    'depends': ['product', 'product_brand', 'stock'],
    'data': [
        'data/report_paper_format.xml',
        'views/product_valuation_view.xml',
        'reports/product_valuation_report_view.xml',
        'views/product_valuation_template.xml',
    ],
    'installable':
    True,
    'auto_install':
    False,
}
