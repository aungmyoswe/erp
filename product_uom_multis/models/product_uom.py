from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_uom_ids = fields.Many2many("product.uom.multi", "product_tmpl_uom_rel", "product_id", "product_uom_id", "Relation Units")
