# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models, _


class report_stock_move_line(models.AbstractModel):
    _name = 'report.product_valutation_report.report_stock_move_line'

    @api.model
    def get_report_values(self, docids, data=None):
        stock_move_line = None
        stock_move_line = self.env['stock.move.line'].search([('id', 'in',
                                                               docids)])
        res = []
        if stock_move_line:
            self._cr.execute(
                '''SELECT pb.name BRAND, pc.name CATEGORY, pt.name PRODUCT,
                sum(sm.do_qty) DOQTY, sum(sm.internal_qty) INTERNALQTY, sum(sm.qty_done) TOTAL FROM stock_move_line sm
                LEFT JOIN product_product pp ON (pp.id = sm.product_id)
                LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                LEFT JOIN product_brand pb ON (pb.id = pt.product_brand_id)
                LEFT JOIN product_category pc ON (pc.id = pt.categ_id)
                WHERE sm.id in %s
                GROUP BY pp.id,pb.name, pc.name, pt.name,pp.default_code
                ORDER BY pp.default_code''', (tuple(docids), ))
            res = self._cr.dictfetchall()
        return {
            'doc_ids': docids,
            'doc_model': 'stock.move.line',
            'docs': stock_move_line,
            'data': data,
            'res': res,
        }
