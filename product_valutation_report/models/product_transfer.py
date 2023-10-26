# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_brand_id = fields.Many2one('product.brand',
                                       string='Brand',
                                       related="product_id.product_brand_id",
                                       help='Select a brand for this product')
    categ_id = fields.Many2one('product.category',
                               'Internal Category',
                               related="product_id.categ_id",
                               help="Select category for the current product")

    do_qty = fields.Float('Do QTY',
                          default=0.0,
                          digits=dp.get_precision('Product Unit of Measure'),
                          compute="compute_do_quantity",
                          store=True,
                          copy=False)

    internal_qty = fields.Float(
        'Internal QTY',
        default=0.0,
        digits=dp.get_precision('Product Unit of Measure'),
        compute="compute_internal_qty",
        store=True,
        copy=False)

    @api.one
    @api.depends('location_dest_id', 'qty_done', 'state')
    def compute_do_quantity(self):
        if self.location_dest_id and self.state == 'done':
            if self.location_dest_id.usage == 'customer':
                self.do_qty = self.qty_done

    @api.one
    @api.depends('location_dest_id', 'qty_done', 'state')
    def compute_internal_qty(self):
        if self.location_dest_id and self.state == 'done':
            if self.location_dest_id.usage == 'internal':
                self.internal_qty = self.qty_done
