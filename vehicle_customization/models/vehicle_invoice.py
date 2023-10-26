import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang
from odoo import tools
from odoo.addons import decimal_precision as dp


class Vehicle_Invoice(models.Model):
    _name = "vehicle.invoice"
    _inherit = ['mail.thread']
    _description = "Vehicle Invoice"
    _order = 'id desc'

    @api.one
    def _compute_total_ctn(self):
        for line in self.invoice_line:
            self.total_of_ctn += line.no_of_ctn

    name = fields.Char(string='Invoice No',
                       required=True,
                       copy=False,
                       readonly=True,
                       index=True,
                       default=lambda self: _('New'))
    car_id = fields.Many2one('res.car',
                             string='Car',
                             change_default=True,
                             ondelete='restrict',
                             required=True)
    driver_id = fields.Many2one('res.driver',
                                string='Driver',
                                change_default=True,
                                ondelete='restrict',
                                required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ],
                             string='Status',
                             readonly=True,
                             copy=False,
                             index=True,
                             default='draft')
    invoice_date = fields.Datetime(string='Date',
                                   required=True,
                                   default=fields.Datetime.now)
    total_of_ctn = fields.Float('Total No.Ctn', compute='_compute_total_ctn')
    invoice_line = fields.One2many('vehicle.invoice.line',
                                   'invoice_id',
                                   string='Invoice Lines',
                                   copy=True,
                                   auto_join=True)
    warehouse_id = fields.Many2one('stock.warehouse',
                                   "Warehouse",
                                   required=True,
                                   store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                        'vehicle.invoice') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'vehicle.invoice') or _('New')
        result = super(Vehicle_Invoice, self).create(vals)
        return result

    @api.multi
    def action_done(self):
        #stock_move_obj = self.env['stock.move']
        for aloop_id in self.invoice_line:
            stock_move_obj = self.env['stock.move'].browse(aloop_id.move_id.id)
            if stock_move_obj.is_delivered is True:
                raise UserError(
                    _("Please check invoice lines. One of the delivery orders that you selected is already delivered."
                      ))
        for a_id in self.invoice_line:
            stock_move_obj = self.env['stock.move'].browse(a_id.move_id.id)
            stock_move_obj.write({'is_delivered': True})
        return self.write({'state': 'done'})


class Vehicle_Invoice_Line(models.Model):
    _name = "vehicle.invoice.line"
    _order = 'id desc'

    name = fields.Text(string='Description')
    invoice_id = fields.Many2one('vehicle.invoice',
                                 string='Vehicle Invoice',
                                 required=True,
                                 ondelete='cascade',
                                 index=True,
                                 copy=False)
    move_id = fields.Many2one('stock.move', string='Stock Move')
    do_number = fields.Char(string='Invoice No')
    partner_id = fields.Many2one('res.partner', string='Partner')
    scheduled_date = fields.Datetime(string='Date')
    origin = fields.Char(string='Description')
    state = fields.Char(string='Status')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
    product_uom_id = fields.Many2one('product.uom', string='UoM')
    location_id = fields.Many2one('stock.location',
                                  string='Destination Location')
    no_of_ctn = fields.Float(string='No.Ctn')


class stock_move(models.Model):
    _inherit = "stock.move"

    is_delivered = fields.Boolean(default=False)


class Delivery_Delivery(models.Model):
    _name = "delivery.delivery"
    _auto = False
    _order = 'id desc'

    do_number = fields.Char(string='Invoice No')
    partner_id = fields.Many2one('res.partner', string='Partner')
    scheduled_date = fields.Datetime(string='Date')
    origin = fields.Char(string='Description')
    state = fields.Char(string='Status')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Quantity')
    product_uom_id = fields.Many2one('product.uom', string='UoM')
    location_id = fields.Many2one('stock.location',
                                  string='Destination Location')
    no_of_ctn = fields.Float(string='No.Ctn')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'delivery_delivery')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW delivery_delivery AS (
              SELECT sm.id,sp.name do_number,sp.partner_id,sp.scheduled_date,sp.origin,sp.state,
                sm.product_id,sm.product_uom_qty,sm.product_uom product_uom_id,sm.location_dest_id location_id, sm.is_delivered, sm.no_of_ctn
                FROM stock_move sm
                INNER JOIN stock_picking sp on sp.id=sm.picking_id
                INNER JOIN stock_picking_type spt on spt.id=sp.picking_type_id
                WHERE sm.is_delivered is not TRUE AND sm.state='done' AND spt.code='outgoing'
                GROUP BY sm.id,sp.name,sp.scheduled_date,sp.partner_id,sp.origin,sp.state,
                sm.product_id,sm.product_uom_qty,sm.product_uom,sm.location_dest_id
            )""")


class delivery_select_wizard(models.TransientModel):
    _name = 'delivery.select.wizard'
    _description = 'Delivery Select Wizard'

    delivery_ids = fields.Many2many('delivery.delivery',
                                    string='Deliver Orders',
                                    copy=False,
                                    required=True)

    @api.one
    def select_delivery(self):
        active_id = self._context['active_id']
        for product_id in self.delivery_ids:
            val = {
                'do_number': product_id.do_number,
                'invoice_id': active_id,
                'move_id': product_id.id,
                'partner_id': product_id.partner_id.id,
                'scheduled_date': product_id.scheduled_date,
                'product_id': product_id.product_id.id,
                'name': product_id.origin,
                'state': product_id.state,
                'product_uom_qty': product_id.product_uom_qty,
                'product_uom_id': product_id.product_uom_id.id,
                'location_id': product_id.location_id.id,
                'no_of_ctn': product_id.no_of_ctn,
            }
            self.env['vehicle.invoice.line'].create(val)
