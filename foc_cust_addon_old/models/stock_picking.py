# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo import tools


class Picking(models.Model):
    _inherit = "stock.picking"

    foc_move_lines = fields.One2many('foc.move.line',
                                     'picking_id',
                                     string="FOC Moves",
                                     copy=True)

    @api.multi
    def action_lines(self):
        if self.delivery_move_lines:
            for dml in self.delivery_move_lines:
                if dml.product_uom_qty > dml.quantity_done:
                    dml.write({'product_uom_qty': dml.quantity_done})
        if self.foc_move_lines:
            for fml in self.foc_move_lines:
                if fml.product_uom_qty > fml.quantity_done:
                    fml.write({'product_uom_qty': fml.quantity_done})
        if self.move_lines:
            for ml in self.move_lines:
                if ml.product_uom_qty:
                    ml.write({'quantity_done': ml.product_uom_qty})

    @api.multi
    def action_backorder(self):
        if self.delivery_move_lines:
            for bdml in self.delivery_move_lines:
                new_qty = 0
                if bdml.product_uom_qty > bdml.quantity_done:
                    new_qty = bdml.product_uom_qty - bdml.quantity_done
                    bdml.write({
                        'product_uom_qty': new_qty,
                        'quantity_done': new_qty,
                        'is_foc': False,
                        'move_line_id': None,
                    })
                else:
                    bdml.unlink()

        if self.foc_move_lines:
            for bfml in self.foc_move_lines:
                fnew_qty = 0
                if bfml.product_uom_qty > bfml.quantity_done:
                    fnew_qty = bfml.product_uom_qty - bfml.quantity_done
                    bfml.write({
                        'product_uom_qty': fnew_qty,
                        'quantity_done': fnew_qty,
                        'is_foc': True,
                        'move_line_id': None,
                    })
                else:
                    bfml.unlink()
        if self.foc_move_lines and self.delivery_move_lines:
            moves_len = len(self.foc_move_lines) + len(
                self.delivery_move_lines)
            if moves_len > len(self.move_lines):
                for mls in self.move_lines:
                    dproduct_id = fproduct_id = None
                    fqty_tot = dqty_tot = 0
                    for fl in self.foc_move_lines:
                        if mls.product_id == fl.product_id and mls.product_uom == fl.product_uom:
                            fproduct_id = fl.product_id
                            fqty_tot = fl.quantity_done
                            # mls.write({'quantity_done': fqty_tot})
                    for dl in self.delivery_move_lines:
                        if mls.product_id == dl.product_id and mls.product_uom == dl.product_uom:
                            dproduct_id = dl.product_id
                            dqty_tot = dl.quantity_done
                            # mls.write({'quantity_done': dqty_tot})
                    if (fqty_tot + dqty_tot
                        ) == mls.product_qty and fproduct_id == dproduct_id:
                        mls.write({
                            'product_uom_qty': dqty_tot,
                            'quantity_done': dqty_tot,
                        })
                        mls.copy({
                            'product_uom_qty': fqty_tot,
                            'quantity_done': fqty_tot,
                        })
                    else:
                        for fl in self.foc_move_lines:
                            if mls.product_id == fl.product_id and mls.product_uom == fl.product_uom:
                                mls.write({'quantity_done': fl.quantity_done})
                        for dl in self.delivery_move_lines:
                            if mls.product_id == dl.product_id and mls.product_uom == dl.product_uom:
                                mls.write({'quantity_done': dl.quantity_done})
                    # if dproduct_id == mls.product_id and mls.product_qty == dqty_tot:
                    #     mls.write({'quantity_done': dqty_tot})
                    # if fproduct_id == mls.product_id and mls.product_qty == fqty_tot:
                    #     mls.write({'quantity_done': fqty_tot})
            else:
                for mls in self.move_lines:
                    fqty_tot = dqty_tot = 0
                    for fl in self.foc_move_lines:
                        if mls.product_id == fl.product_id and mls.product_uom == fl.product_uom:
                            mls.write({'quantity_done': fl.quantity_done})
                    for dl in self.delivery_move_lines:
                        if mls.product_id == dl.product_id and mls.product_uom == dl.product_uom:
                            mls.write({'quantity_done': dl.quantity_done})
        else:
            for mls in self.move_lines:
                for fl in self.foc_move_lines:
                    if mls.product_id == fl.product_id and mls.product_uom == fl.product_uom:
                        mls.write({'quantity_done': fl.quantity_done})
                for dl in self.delivery_move_lines:
                    if mls.product_id == dl.product_id and mls.product_uom == dl.product_uom:
                        mls.write({'quantity_done': dl.quantity_done})


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        self.pick_ids.action_done()
        self.pick_ids.action_lines()
        picking_id = self.env['stock.picking'].search([('backorder_id', '=',
                                                        self.pick_ids.id)])
        if picking_id:
            picking_id.action_backorder()
        if cancel_backorder:
            for pick_id in self.pick_ids:
                backorder_pick = self.env['stock.picking'].search([
                    ('backorder_id', '=', pick_id.id)
                ])
                backorder_pick.action_cancel()
                pick_id.message_post(
                    body=_("Back order <em>%s</em> <b>cancelled</b>.") %
                    (",".join([b.name or '' for b in backorder_pick])))
