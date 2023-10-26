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

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class Driver(models.Model):
    _name = "res.driver"
    _inherit = ['mail.thread']
    _description = "Driver"
    _order = 'id desc'
    
    name = fields.Char(string='Driver Name', required=True, copy=False, index=True)
    phone_no = fields.Char(string='Phone No')
    address = fields.Char(string='Address')
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")
    
    