from odoo import fields, models, api, tools, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cashbook_id = fields.Many2one("cash.book", "Cashbook Item")

    def create(self, values):
        res = super(AccountMoveLine, self).create(values)
        cash_id = None
        if res and res.user_type_id.type == 'liquidity':
            if res.user_type_id.name == 'Bank and Cash':
                cash_id = self.env['cash.book'].search([('name', '=', res.date)])
                if cash_id:
                    res.write({'cashbook_id': cash_id.id})
                else:
                    cash_id = self.env['cash.book'].create({'name': res.date})
                    res.write({'cashbook_id': cash_id.id})
        return res


class CashBook(models.Model):
    _name = "cash.book"

    def _get_currency(self):
        if not self.currency_id:
            return self.env.user.company_id.currency_id

    name = fields.Date("Date")
    opening_balance = fields.Monetary("Opening",
                                      default=0,
                                      compute="_compute_total",
                                      store=True)
    closing_balance = fields.Monetary("Closing",
                                      compute="_compute_total",
                                      store=True)

    debit_total = fields.Monetary("Daily Total",
                                  compute="_compute_total",
                                  store=True)
    credit_total = fields.Monetary("Credit Daily Total",
                                   compute="_compute_total",
                                   store=True)
    daily_balance = fields.Monetary("Daily Balance",
                                    compute="_compute_total",
                                    store=True)
    is_opening_debit = fields.Boolean("Is Opening Debit",
                                      compute="_compute_total",
                                      store=True)
    is_debit = fields.Boolean("Is Debit",
                              default=True,
                              compute="_compute_total",
                              store=True)
    is_closing_debit = fields.Boolean("Is Debit",
                                      compute="_compute_total",
                                      store=True)
    total_debit = fields.Monetary("Total",
                                  compute="_compute_total",
                                  store=True)
    total_credit = fields.Monetary("Total Credit",
                                   compute="_compute_total",
                                   store=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=_get_currency,
        help="The optional other currency if it is a multi-currency entry.")
    cashbook_line = fields.One2many("account.move.line", 'cashbook_id',
                                    "Cashbook item")

    @api.depends('cashbook_line.debit', 'cashbook_line.credit',
                 'opening_balance', 'closing_balance', 'is_debit',
                 'is_closing_debit', 'is_opening_debit')
    @api.one
    def _compute_total(self):
        cash_ids = self.search([('name', '<', self.name)], order="name desc")
        if cash_ids:
            cash_id = self.browse(cash_ids[0]).id
            self.opening_balance = cash_id.closing_balance
            self.is_opening_debit = cash_id.is_closing_debit
        else:
            self.opening_balance = self.env.user.company_id.opening_balance
            if self.env.user.company_id.is_credit == True:
                self.is_debit = False
                self.is_opening_debit = False
            else:
                self.is_debit = True
                self.is_opening_debit = True
        credit = debit = 0
        if self.cashbook_line:
            for line in self.cashbook_line:
                debit += line.debit
                credit += line.credit
            self.debit_total = debit
            self.credit_total = credit
            if debit > credit:
                self.daily_balance = debit - credit
                self.is_debit = True
            if debit < credit:
                self.daily_balance = credit - debit
                self.is_debit = False
            if self.is_opening_debit == True:
                self.total_debit = debit + self.opening_balance
                self.total_credit = credit
            if self.is_opening_debit == False:
                self.total_credit = credit + self.opening_balance
                self.total_debit = debit
            if self.total_debit > self.total_credit:
                self.closing_balance = self.total_debit - self.total_credit
                self.is_closing_debit = True
            if self.total_debit < self.total_credit:
                self.closing_balance = self.total_credit - self.total_debit
                self.is_closing_debit = False

    # @api.multi
    # def unlink(self):
    #     if self.cashbook_line:
    #         raise UserError(
    #             _('You cannot remove/delete account move line in this cashbook.'
    #               ))
    #     return super(CashBook, self).unlink()
