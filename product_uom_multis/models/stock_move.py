from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    product_uom_re_id = fields.Many2one("product.uom.multi",
                                        "Relation",
                                        readonly=True)

    @api.onchange('product_uom')
    def onchange_product_uom(self):
        if self.product_id.product_uom_ids:
            for uom in self.product_id.product_uom_ids:
                self.product_uom_re_id = self.env['product.uom.multi'].search([
                    ('from_unit', '=', self.product_uom.id)
                ]).id
        if self.product_uom.factor > self.product_id.uom_id.factor:
            return {
                'warning': {
                    'title':
                    "Unsafe unit of measure",
                    'message':
                    _("You are using a unit of measure smaller than the one you are using in "
                      "order to stock your product. This can lead to rounding problem on reserved quantity! "
                      "You should use the smaller unit of measure possible in order to valuate your stock or "
                      "change its rounding precision to a smaller value (example: 0.00001)."
                      ),
                }
            }

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id.with_context(
            lang=self.partner_id.lang or self.env.user.lang)
        self.name = product.partner_ref
        self.product_uom = product.uom_id.id
        puom = []
        if product.product_uom_ids:
            for u in product.product_uom_ids:
                puom.append(u.from_unit.id)
        return {'domain': {'product_uom': [('id', 'in', puom)]}}