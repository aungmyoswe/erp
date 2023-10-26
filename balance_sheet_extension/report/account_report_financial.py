# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([
            ('id', '=', data['account_report_id'][0])
        ])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(
            data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get(
                'comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get(
                            'account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name':
                report.name,
                'balance':
                res[report.id]['balance'] * report.sign,
                'type':
                'report',
                'level':
                bool(report.style_overwrite) and report.style_overwrite
                or report.level,
                'account_type':
                report.type
                or False,  #used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name':
                        account.code + ' ' + account.name,
                        'balance':
                        value['balance'] * report.sign or 0.0,
                        'type':
                        'account',
                        'level':
                        report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type':
                        account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']
                        ) or not account.company_id.currency_id.is_zero(
                                vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(
                            vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(
                                vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
        if lines:
            for line in lines:
                if line['name'] == 'Cash in Hand':
                    if self.env.user.company_id.is_credit == True:
                        if 'credit' in line:
                            line[
                                'credit'] += self.env.user.company_id.opening_balance
                    else:
                        if 'debit' in line:
                            line[
                                'debit'] += self.env.user.company_id.opening_balance

                    if 'credit' in line or 'debit' in line:
                        line['balance'] = line['debit'] - line['credit']
                    else:
                        if self.env.user.company_id.is_credit == True:
                            line['balance'] = line[
                                'balance'] - self.env.user.company_id.opening_balance
                        if self.env.user.company_id.is_credit != True:
                            line['balance'] = line[
                                'balance'] + self.env.user.company_id.opening_balance
                    for ass in lines:
                        if ass['name'] == 'Assets':
                            if 'credit' in line:
                                ass['credit'] += line['credit']
                                ass['balance'] -= line['credit']
                            if 'debit' in line:
                                ass['debit'] += line['debit']
                                ass['balance'] += line['debit']
                            else:
                                if self.env.user.company_id.is_credit == True:
                                    ass['balance'] = ass['balance'] + line[
                                        'balance']
                                if self.env.user.company_id.is_credit != True:
                                    ass['balance'] = ass['balance'] + line[
                                        'balance']

        return lines
