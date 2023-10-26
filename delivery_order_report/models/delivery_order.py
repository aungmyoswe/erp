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

class Delivery_Order(models.Model):
    _name = "delivery.order"
    _auto = False
    _order = 'id desc'

    do_number = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner',string='Customer')
    backorder_id = fields.Many2one('stock.picking',string='Backorder No')
    date = fields.Datetime(string='Date')
    state = fields.Char(string='Status')
    product_id = fields.Many2one('product.product',string='Product')
    product_qty = fields.Float(string='Quantity')
    location_id = fields.Many2one('stock.location',string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    onhand_qty = fields.Float(string='Onhand Quantity')
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'delivery_delivery')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW delivery_order AS (
                SELECT sm.id,sm.date,sp.name do_number,sp.partner_id,pp.id product_id,sp.backorder_id,sm.product_qty,
                CASE WHEN sp.state='draft' THEN 'Draft'
                WHEN sp.state='waiting' THEN 'Waiting Another Operation'
                WHEN sp.state='confirmed' THEN 'Waiting'
                WHEN sp.state='assigned' THEN 'Ready'
                WHEN sp.state='done' THEN 'Done'
                WHEN sp.state='cancel' THEN 'Cancelled' END::character varying state,
                sm.location_id,sm.location_dest_id,COALESCE(quant.quantity,0.0) onhand_qty  
                FROM stock_move sm
                INNER JOIN stock_picking sp ON sp.id=sm.picking_id
                INNER JOIN product_product pp ON sm.product_id=pp.id
                INNER JOIN product_template pt ON pp.product_tmpl_id=pt.id
                INNER JOIN stock_location sls ON sls.id=sm.location_id
                INNER JOIN stock_location sld ON sld.id=sm.location_dest_id
                INNER JOIN res_partner rp ON rp.id=sp.partner_id
                INNER JOIN stock_picking_type spt ON spt.id=sp.picking_type_id
                LEFT JOIN (select sum(quantity) quantity,product_id from stock_quant where location_id in (select id From stock_location where usage in ('internal'))
                group by product_id)quant ON quant.product_id=sm.product_id
                WHERE spt.code='outgoing'
            )""")
    