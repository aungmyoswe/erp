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


class Branch(models.Model):
    _name = "res.branch"

    code = fields.Char(string='Code', required=True,)
    name = fields.Char(string='Name', required=True)
    address_in_english = fields.Text(string='Address In English')
    address_in_myanmar = fields.Text(string='Address In Myanmar')
    company_id = fields.Many2one('res.company', string='Company')