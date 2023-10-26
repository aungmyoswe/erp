# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name':
    'Product UOM Extension',
    'version':
    '0.1.6',
    'category':
    'Inventory',
    'summary':
    "Product UOM Extension",
    'author':
    'Aung Myo Swe',
    'license':
    'AGPL-3',
    'depends': ['base','product','stock','stock_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_uom_view.xml',
        'views/product_extension.xml',
    ],
    'installable':
    True,
    'auto_install':
    False,
}
