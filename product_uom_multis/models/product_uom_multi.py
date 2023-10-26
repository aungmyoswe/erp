from odoo import api, fields, models


class ProductUomMulti(models.Model):
    _name = "product.uom.multi"

    name = fields.Char("Name", default="New", compute="get_name", search='_search_name', store=True)
    from_unit = fields.Many2one("product.uom", string="")
    amount = fields.Float("Equal", related="from_unit.factor_inv", store=True)
    to_unit = fields.Many2one("product.uom", string="")
    product_tmpl_id = fields.Many2one("product.template", "Product Template")

    def _search_name(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('name', operator, value)]
    
    @api.one
    @api.depends('amount', 'from_unit', 'to_unit')
    def get_name(self):
        if self.from_unit and self.amount and self.to_unit:
            self.name = self.from_unit.name + '=' + str(self.amount) + self.to_unit.name
        else:
            self.name = "New"

    @api.onchange('from_unit')
    def onchange_from_unit(self):
        if self.product_tmpl_id:
            uom_ids = []
            for pid in self.product_tmpl_id:
                uom_ids = self.env['product.uom'].search([('category_id', '=' , pid.uom_po_id.id)])
            return {'domain': {'from_unit': [('id', 'in', uom_ids.ids)]}}
            