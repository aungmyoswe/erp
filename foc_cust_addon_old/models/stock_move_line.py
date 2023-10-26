from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo import tools


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    is_foc = fields.Boolean("FOC",
                            default=False,
                            compute="get_is_foc",
                            store=True)

    @api.one
    @api.depends('move_id')
    def get_is_foc(self):
        for move in self:
            if move.is_foc == False and self.picking_id.foc_move_lines:
                for foc in self.picking_id.foc_move_lines:
                    if foc.product_id == self.product_id and foc.quantity_done == self.qty_done:
                        move.is_foc = True
