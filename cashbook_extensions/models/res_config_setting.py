# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    opening_balance = fields.Float(string='Opening Balance', store=True)
    is_credit = fields.Boolean('Is Credit', store=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    opening_balance = fields.Float(string='Opening Balance',
                                   compute='_compute_opening_balance',
                                   store=True,
                                   readonly=False)
    is_credit = fields.Boolean("Is Credit",
                               compute='_compute_opening_balance',
                               store=True,
                               readonly=False)

    @api.one
    @api.depends('company_id')
    def _compute_opening_balance(self):
        self.opening_balance = self.company_id.opening_balance
        self.is_credit = self.company_id.is_credit

    @api.model
    def create(self, values):
        if ('company_id' in values and 'currency_id' in values):
            company = self.env['res.company'].browse(values.get('company_id'))
            if company.currency_id.id == values.get('currency_id'):
                values.pop('currency_id')
            if company.accounts_code_digits == values.get('code_digits'):
                values.pop('code_digits')
            if values['is_credit'] or values['opening_balance']:
                company.is_credit = values['is_credit']
                company.opening_balance = values['opening_balance']
        return super(ResConfigSettings, self).create(values)
