from odoo import api, fields, models, _
from odoo import tools


class Vehicle_Invoice_Line(models.Model):
    _inherit = "vehicle.invoice.line"

    is_foc = fields.Boolean("FOC")
    move_id = fields.Many2one('stock.move', "Move")
    move_line_id = fields.Many2one('stock.move.line', "Move Line")


class Delivery_Delivery(models.Model):
    _inherit = "delivery.delivery"

    is_foc = fields.Boolean("Foc")
    move_id = fields.Many2one('stock.move', "Move")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'delivery_delivery')
        self.env.cr.execute("""
             CREATE OR REPLACE VIEW delivery_delivery AS (
                    SELECT sml.id, sm.id move_id,sp.name do_number,sp.partner_id,sp.scheduled_date,sp.origin,sp.state,
                    sml.product_id,sml.is_foc,sml.do_qty product_uom_qty,sm.product_uom product_uom_id,sml.location_dest_id location_id, sm.is_delivered, sm.no_of_ctn
                    FROM  stock_move_line sml
                    INNER JOIN stock_move sm on sml.move_id = sm.id
                    INNER JOIN stock_picking sp on sp.id=sm.picking_id
                    INNER JOIN stock_picking_type spt on spt.id=sp.picking_type_id
                    WHERE sm.is_delivered is not TRUE AND sm.state='done' AND spt.code='outgoing'
                    GROUP BY sml.id,sp.name,sp.scheduled_date,sp.partner_id,sp.origin,sp.state,
                    sml.product_id,sm.id,sml.do_qty,sml.is_foc,sm.product_uom,sml.location_dest_id,sm.is_delivered,sm.no_of_ctn)"""
                            )


class delivery_select_wizard(models.TransientModel):
    _inherit = 'delivery.select.wizard'

    @api.one
    def select_delivery(self):
        active_id = self._context['active_id']
        for product_id in self.delivery_ids:
            val = {
                'do_number': product_id.do_number,
                'invoice_id': active_id,
                'move_id': product_id.move_id.id,
                'move_line_id': product_id.id,
                'partner_id': product_id.partner_id.id,
                'scheduled_date': product_id.scheduled_date,
                'product_id': product_id.product_id.id,
                'name': product_id.origin,
                'state': product_id.state,
                'product_uom_qty': product_id.product_uom_qty,
                'product_uom_id': product_id.product_uom_id.id,
                'location_id': product_id.location_id.id,
                'no_of_ctn': product_id.no_of_ctn,
                'is_foc': product_id.is_foc,
            }
            self.env['vehicle.invoice.line'].create(val)
