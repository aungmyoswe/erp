# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo import tools


class StockMove(models.Model):
    _inherit = "stock.move"

    is_foc = fields.Boolean("FOC", default=False, store=True)

    @api.model
    def create(self, vals):
        perform_tracking = not self.env.context.get(
            'mail_notrack') and vals.get('picking_id')
        if perform_tracking:
            picking = self.env['stock.picking'].browse(vals['picking_id'])
            initial_values = {picking.id: {'state': picking.state}}
        if not 'name' in vals:
            product_id = self.env['product.product'].search([
                ('id', '=', vals['product_id'])
            ])
            vals['name'] = product_id.product_tmpl_id.name
            vals['location_id'] = picking.location_id.id
            vals['location_dest_id'] = picking.location_dest_id.id
        vals['ordered_qty'] = vals.get('product_uom_qty')
        res = super(StockMove, self).create(vals)
        if perform_tracking:
            picking.message_track(picking.fields_get(['state']),
                                  initial_values)
        return res

    def _quantity_done_set(self):
        quantity_done = self[
            0].quantity_done  # any call to create will invalidate `move.quantity_done`
        for move in self:
            move_lines = move._get_move_lines()
            if not move_lines:
                if quantity_done:
                    # do not impact reservation here
                    move_line = self.env['stock.move.line'].create(
                        dict(move._prepare_move_line_vals(),
                             qty_done=quantity_done))
                    move.write({'move_line_ids': [(4, move_line.id)]})
            elif len(move_lines) == 1:
                move_lines[0].qty_done = quantity_done
            else:
                if self.picking_id.foc_move_lines and self.picking_id.delivery_move_lines:
                    move_id1 = self.env['stock.move.line'].browse(
                        move_lines[0].id)
                    for sml in move_id1:
                        sml.qty_done = 0
                        for dml in self.picking_id.delivery_move_lines:
                            if sml.product_id == dml.product_id:
                                sml.qty_done += dml.quantity_done
                                sml.is_foc = False
                    move_id2 = self.env['stock.move.line'].browse(
                        move_lines[1].id)
                    for sml in move_id2:
                        sml.qty_done = 0
                        for fml in self.picking_id.foc_move_lines:
                            if sml.product_id == fml.product_id:
                                sml.qty_done += fml.quantity_done
                                sml.is_foc = True
                else:
                    raise UserError(
                        "Cannot set the done quantity from this stock move, work directly with the move lines."
                    )
