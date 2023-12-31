import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp


class Car(models.Model):
    _name = "res.car"
    _inherit = ['mail.thread']
    _description = "Car"
    _order = 'id desc'
    
    
    name = fields.Char(string='Car No', required=True, copy=False, index=True)
    