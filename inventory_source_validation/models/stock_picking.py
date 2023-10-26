# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        # validation source doc
        picks = self.search([('origin', '=', vals['origin'])])
        if len(picks) == 1:
            if 'backorder_id' not in vals and picks.picking_type_id.id == vals[
                    'picking_type_id']:
                raise UserError(
                    _("Source Document %s exiting in Database.") %
                    (vals['origin']))
        if len(picks) > 1:
            for pic in picks:
                if 'backorder_id' not in vals and pic.picking_type_id.id == vals[
                        'picking_type_id']:
                    raise UserError(
                        _("Source Document %s exiting in Database.") %
                        (vals['origin']))
        # TDE FIXME: clean that brol
        defaults = self.default_get(['name', 'picking_type_id'])
        if vals.get('name', '/') == '/' and defaults.get(
                'name', '/') == '/' and vals.get(
                    'picking_type_id', defaults.get('picking_type_id')):
            vals['name'] = self.env['stock.picking.type'].browse(
                vals.get(
                    'picking_type_id',
                    defaults.get('picking_type_id'))).sequence_id.next_by_id()

        # TDE FIXME: what ?
        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        if vals.get('move_lines') and vals.get('location_id') and vals.get(
                'location_dest_id'):
            for move in vals['move_lines']:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
        res = super(Picking, self).create(vals)
        res._autoconfirm_picking()
        return res