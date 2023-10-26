# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo import tools


class Picking(models.Model):
    _inherit = "stock.picking"

    delivery_move_lines = fields.One2many('delivery.move.line',
                                          'picking_id',
                                          string="Delivery Moves",
                                          copy=True)


class DeliveryMoveLine(models.Model):
    _name = "delivery.move.line"

    picking_id = fields.Many2one('stock.picking', "Stock Picking")
    product_id = fields.Many2one('product.product', "Product")
    product_uom = fields.Many2one('product.uom',
                                  'Unit of Measure',
                                  required=True)
    product_uom_qty = fields.Float(
        'Initial Demand',
        digits=0,
        default=0,
        store=True,
        help='Quantity in the default UoM of the product')
    product_uom_re_id = fields.Many2one("product.uom.multi", "Relation")
    no_of_ctn = fields.Float('No.Ctn')
    move_id = fields.Many2one("stock.move", "Move", store=True)
    location_id = fields.Many2one('stock.location',
                                  'Source Location',
                                  auto_join=True,
                                  index=True)
    location_dest_id = fields.Many2one(
        'stock.location',
        'Destination Location',
        auto_join=True,
        index=True,
        help="Location where the system will stock the finished products.")
    quantity_done = fields.Float("Done")
    is_foc = fields.Boolean("FOC", default=False, store=True)
    show_details_visible = fields.Boolean('Details Visible')
    show_reserved_availability = fields.Boolean('From Supplier')
    is_locked = fields.Boolean(readonly=True)
    reserved_availability = fields.Float(
        'Quantity Reserved',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
        help='Quantity that has already been reserved for this move')
    scrapped = fields.Boolean('Scrapped',
                              related='location_dest_id.scrap_location',
                              readonly=True,
                              store=True)
    state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'),
                              ('waiting', 'Waiting Another Move'),
                              ('confirmed', 'Waiting Availability'),
                              ('partially_available', 'Partially Available'),
                              ('assigned', 'Available'), ('done', 'Done')],
                             string='Status',
                             copy=False,
                             default='draft',
                             index=True,
                             readonly=True)
    move_line_id = fields.Many2one("stock.move.line", "Move Line", store=True)

    @api.onchange('quantity_done')
    def onchange_quantity_done(self):
        if self.quantity_done:
            if self.picking_id.foc_move_lines:
                for l in self.picking_id.move_lines:
                    if l.product_id == self.product_id:
                        l.write({'quantity_done': self.quantity_done})
                for ml in self.picking_id.move_line_ids:
                    if ml.product_id == self.product_id:
                        ml.write({'qty_done': self.quantity_done})

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_id.product_uom_ids:
            for uom in self.product_id.product_uom_ids:
                self.product_uom_re_id = self.env['product.uom.multi'].search([
                    ('from_unit', '=', self.product_uom.id)
                ]).id
        if self.product_uom.factor > self.product_id.uom_id.factor:
            return {
                'warning': {
                    'title':
                    "Unsafe unit of measure",
                    'message':
                    _("You are using a unit of measure smaller than the one you are using in "
                      "order to stock your product. This can lead to rounding problem on reserved quantity! "
                      "You should use the smaller unit of measure possible in order to valuate your stock or "
                      "change its rounding precision to a smaller value (example: 0.00001)."
                      ),
                }
            }

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        self.product_uom = product.uom_id.id
        puom = []
        if product.product_uom_ids:
            for u in product.product_uom_ids:
                puom.append(u.from_unit.id)
        return {'domain': {'product_uom': [('id', 'in', puom)]}}

    @api.model
    def create(self, vals):
        pick_id = self.env['stock.picking'].search([('id', '=',
                                                     vals['picking_id'])])
        if not pick_id.backorder_id:
            stock_move_id = self.env['stock.move'].create(vals)
            vals['move_id'] = stock_move_id.id
            vals['move_line_id'] = stock_move_id.move_line_ids.id
            if stock_move_id.move_line_ids.is_foc == True:
                stock_move_id.move_line_ids.is_foc = False
        return super(DeliveryMoveLine, self).create(vals)
