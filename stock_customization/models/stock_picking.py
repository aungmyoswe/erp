# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import namedtuple
import json
import time

from itertools import groupby
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from operator import itemgetter

class Picking(models.Model):
    _inherit = "stock.picking"

    @api.one
    def _compute_total_ctn(self):
        for line in self.move_lines:
            self.total_of_ctn += line.no_of_ctn
        
    origin = fields.Char(
        'Source Document', required=True, index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Reference of the document")
    total_of_ctn = fields.Float('Total No.Ctn', compute='_compute_total_ctn')

class StockMove(models.Model):
    _inherit = "stock.move"

    no_of_ctn = fields.Float('No.Ctn')