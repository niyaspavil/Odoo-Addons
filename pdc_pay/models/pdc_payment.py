from openerp import api, fields, models, _
from openerp.exceptions import UserError


class Bank(models.Model):
    _inherit = 'res.bank'

    branch = fields.Char(string="Branch")


class ChequeType(models.Model):
    _name = 'cheque.type'

    name = fields.Char(string="Cheque Type", required=True)
    code = fields.Char(string="Cheque Code")


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_name = fields.Many2one('res.bank', string="Bank", required=True)
    cheque_number = fields.Char(strig='Cheque Number', required=True)
    clearing_date = fields.Date(strig='Clearing Date', required=True)
    cheque_type = fields.Many2one('cheque.type', string="Cheque Type", required=True)
    branch = fields.Char(string="Branch", required=True)




# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     related_pdc = fields.Many2one('pdc.payment', invisible=True)
    # related_payment = fields.Many2one('pdc.payment', invisible=True)


# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     related_pdc_re = fields.Many2one('pdc.payment', invisible=True)

#
# class AccountPayment(models.Model):
#     _inherit = 'account.partner'
#
#     related_pdc_re = fields.Many2one('pdc.payment', invisible=True)


class PdcPay(models.Model):
    _name = 'pdc.payment'
    _inherit = 'account.payment'

    # states = {'running': [('readonly', True)], 'done': [('readonly', True)]}

    related_inv_ids = fields.Many2one('account.invoice', string="Related Invoice", required=True)
    destination_account_id = fields.Many2one('account.account', compute='_compute_destination_account_id', readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('rejected', 'Rejected'),
                              ('accepted', 'Accepted'),
                              ('posted', 'Posted'),
                              ('sent', 'Sent'),
                              ('reconciled', 'Reconciled')],
                             readonly=True, default='draft', copy=False, string="Status")

    @api.onchange('bank_name')
    def onchange_bank_name(self):
        print "232323232ffffffffffffffff"
        if self.bank_name:
            print "Gggggg", self.bank_name.branch
            self.branch = self.bank_name.branch

    @api.one
    def action_confirm(self):
        self.state = 'confirm'

    @api.one
    @api.depends('related_inv_ids')
    def _compute_destination_account_id(self):
        print "22222CPMMMMMMMMMMMM"
        print "222CPMMMMMMMMMMM1", self.invoice_ids
        print "222CPMMMMMMMMMMM2", self.partner_id
        if self.related_inv_ids:
            self.destination_account_id = self.related_inv_ids[0].account_id.id
            print "ff11"
        elif self.payment_type == 'transfer':
            if not self.company_id.transfer_account_id.id:
                raise UserError(_('Transfer account not defined on the company.'))
            self.destination_account_id = self.company_id.transfer_account_id.id
        elif self.partner_id:
            print "ffff2222"
            if self.partner_type == 'customer':
                print "fff33333"
                self.destination_account_id = self.partner_id.property_account_receivable_id.id
            else:
                print "f4444"
                self.destination_account_id = self.partner_id.property_account_payable_id.id

        print "222cpmout", self.destination_account_id

    @api.one
    def action_reject(self):
        self.state = 'rejected'

    @api.one
    def action_accept(self):
        print"34545353536"
        # register_payment = self.pool('account.payment')
        # print "@@@@", self.pool('account.payment').browse(self.cr,)
        browser = self.pool['account.payment'].browse(self._cr, self._uid, self._ids)
        if self.payment_type == 'inbound':
            self.partner_type = 'customer'
        elif self.payment_type == 'outbound':
            self.partner_type = 'supplier'



        if self.payment_type == 'transfer':
            sequence_code = 'account.payment.transfer'
        else:
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    sequence_code = 'account.payment.customer.invoice'
                if self.payment_type == 'outbound':
                    sequence_code = 'account.payment.customer.refund'
            if self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    sequence_code = 'account.payment.supplier.refund'
                if self.payment_type == 'outbound':
                    sequence_code = 'account.payment.supplier.invoice'

        print self.payment_type
        print self.payment_method_id
        print self.amount
        print self.payment_date
        print self.journal_id
        print self.partner_type
        print self.destination_account_id
        print"poooled1111", browser

        print self.related_inv_ids

        # for inv in self.related_inv_ids:
        self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(sequence_code)

        print "llllLL", self.name
        print "invoivvvvvvvvvvvvvv", self.related_inv_ids.amount_total




        pdc_payment_vals = {
            'name': self.name,
            # 'state': 'posted',
            'payment_type': self.payment_type,
            'journal_id': self.journal_id.id,
            'invoice_ids': [20],
            'amount': self.amount,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'partner_type': self.partner_type,
            'destination_account_id': self.destination_account_id.id,
        }
        print"haiiiiiiiiiiiii", pdc_payment_vals
        xx = self.env['account.payment'].create(pdc_payment_vals)
        # payment = self.env['account.payment'].create(self.get_payment_vals())
        print "yyyy",xx
        xx.post()
        print " crrreated"

        # self.state = 'accepted'
