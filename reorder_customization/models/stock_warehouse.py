from odoo import api, fields, models


class Orderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"

    onhand_qty = fields.Float("On Hand", compute="_compute_onhand_qty")

    @api.one
    @api.depends('product_id', 'location_id')
    def _compute_onhand_qty(self):
        if self.product_id and self.location_id:
            stock_quant_ids = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id)
            ])
            if stock_quant_ids:
                self.onhand_qty = stock_quant_ids.quantity
            else:
                self.onhand_qty = 0