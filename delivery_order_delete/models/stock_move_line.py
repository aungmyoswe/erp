# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def unlink(self):
        backorder_id = self.search([('backorder_id', '=', self.id)])
        if backorder_id:
            raise ValidationError(_("Firstly delete back order."))
        self.mapped('move_lines')._action_cancel()
        self.mapped('move_lines').unlink()  # Checks if moves are not done
        return super(Picking, self).unlink()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def unlink(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        d_qty = res_qty = 0
        for ml in self:
            if ml.qty_done and ml.location_id:
                quant_id = self.env['stock.quant'].search([
                    ('product_id', '=', ml.product_id.id),
                    ('location_id', '=', ml.location_id.id)
                ])
                uom_id = self.env['product.uom'].browse(ml.product_uom_id.id)
                if uom_id.uom_type == 'bigger':
                    d_qty = ml.qty_done * uom_id.factor_inv
                    if ml.product_uom_qty and ml.state != 'done':
                        res_qty = ml.product_uom_qty * uom_id.factor_inv
                if uom_id.uom_type == 'smaller':
                    d_qty = ml.qty_done * uom_id.factor
                    if ml.product_uom_qty and ml.state != 'done':
                        res_qty = ml.product_uom_qty * uom_id.factor
                if uom_id.uom_type == 'reference':
                    d_qty = ml.qty_done
                    if ml.product_uom_qty and ml.state != 'done':
                        res_qty = ml.product_uom_qty
                if ml.state == 'draft':
                    quant_id.write({'quantity': quant_id.quantity + d_qty})
                if ml.state == 'assigned':
                    quant_id.write({
                        'reserved_quantity':
                        quant_id.reserved_quantity - res_qty
                    })
            if ml.state in ('done', 'cancel'):
                ml.write({'state': 'draft'})
                ml.unlink()
            #     raise UserError(
            #         _('You can not delete product moves if the picking is done. You can only correct the done quantities.'
            #           ))
            # Unlinking a move line should unreserve.
            if ml.product_id.type == 'product' and not ml.location_id.should_bypass_reservation(
            ) and not float_is_zero(ml.product_qty,
                                    precision_digits=precision):
                try:
                    self.env['stock.quant']._update_reserved_quantity(
                        ml.product_id,
                        ml.location_id,
                        -ml.product_qty,
                        lot_id=ml.lot_id,
                        package_id=ml.package_id,
                        owner_id=ml.owner_id,
                        strict=True)
                except UserError:
                    if ml.lot_id:
                        self.env['stock.quant']._update_reserved_quantity(
                            ml.product_id,
                            ml.location_id,
                            -ml.product_qty,
                            lot_id=False,
                            package_id=ml.package_id,
                            owner_id=ml.owner_id,
                            strict=True)
                    else:
                        raise
        moves = self.mapped('move_id')
        res = super(StockMoveLine, self).unlink()
        if moves:
            moves._recompute_state()
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        # if any(move.state == 'done' for move in self):
        #     raise UserError(
        #         _('You cannot cancel a stock move that has been set to \'Done\'.'
        #           ))
        moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
        # self cannot contain moves that are either cancelled or done, therefore we can safely
        # unlink all associated move_line_ids
        moves_to_cancel._do_unreserve()

        for move in moves_to_cancel:
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') -
                               move).mapped('state')
            if move.propagate:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids.filtered(
                        lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel')
                       for state in siblings_states):
                    move.move_dest_ids.write(
                        {'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write(
                        {'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True

    def _do_unreserve(self):
        moves_to_unreserve = self.env['stock.move']
        for move in self:
            if move.state == 'cancel':
                # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
                continue
            if move.state == 'done':
                if move.scrapped:
                    # We may have done move in an open picking in a scrap scenario.
                    continue
                else:
                    # raise UserError(_('Cannot unreserve a done move'))
                    move.write({'state': 'draft'})
            moves_to_unreserve |= move
        moves_to_unreserve.mapped('move_line_ids').unlink()
        return True


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_reserved_quantity(self,
                                  product_id,
                                  location_id,
                                  quantity,
                                  lot_id=None,
                                  package_id=None,
                                  owner_id=None,
                                  strict=False):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id,
                              location_id,
                              lot_id=lot_id,
                              package_id=package_id,
                              owner_id=owner_id,
                              strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = self._get_available_quantity(
                product_id,
                location_id,
                lot_id=lot_id,
                package_id=package_id,
                owner_id=owner_id,
                strict=strict)
            # if float_compare(quantity,
            #                  available_quantity,
            #                  precision_rounding=rounding) > 0:
            #     raise UserError(
            #         _('It is not possible to reserve more products of %s than you have in stock.'
            #           ) % product_id.display_name)
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            # if float_compare(abs(quantity),
            #                  available_quantity,
            #                  precision_rounding=rounding) > 0:
            #     raise UserError(
            #         _('It is not possible to unreserve more products of %s than you have in stock.'
            #           ) % product_id.display_name)
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant,
                                 0,
                                 precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity,
                                            abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(
                    quantity, precision_rounding=rounding) or float_is_zero(
                        available_quantity, precision_rounding=rounding):
                break
        return reserved_quants
