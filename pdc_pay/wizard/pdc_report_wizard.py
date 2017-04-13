# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.exceptions import UserError


# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#     related_pdc_re = fields.Many2one('pdc.payment.report', invisible=True)


class PdcReports(models.TransientModel):
    _name = 'pdc.payment.report'
    _description = 'PDC Report'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    partner_ids = fields.Many2many('res.partner', string='Partners')
    state = fields.Selection([('draft', 'D32raft'),
                              ('confirm', 'Confirm'),
                              ('rejected', 'Rejected'),
                              ('accepted', 'Accepted')],
                             default='confirm', copy=False, string="Status")
    #
    # def _print_report(self, data):
    #     res = {}
    #     data = self.pre_print_report(data)
    #     data['form'].update(self.read(['period_length'])[0])
    #     period_length = data['form']['period_length']
    #     if period_length<=0:
    #         raise UserError(_('You must set a period length greater than 0.'))
    #     if not data['form']['date_from']:
    #         raise UserError(_('You must set a start date.'))
    #
    #     start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")
    #
    #     for i in range(5)[::-1]:
    #         stop = start - relativedelta(days=period_length - 1)
    #         res[str(i)] = {
    #             'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
    #             'stop': start.strftime('%Y-%m-%d'),
    #             'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
    #         }
    #         start = stop - relativedelta(days=1)
    #     data['form'].update(res)
    #     return self.env['report'].with_context(landscape=True).get_action(self, 'account.report_agedpartnerbalance', data=data)
