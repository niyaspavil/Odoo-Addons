from openerp.osv import osv, fields
from openerp import api
import logging

_logger = logging.getLogger(__name__)

class AcquirerPaypal(osv.Model):
    _inherit = 'payment.acquirer'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),

    }


class PaymentTransaction(osv.Model):
    _inherit = 'payment.transaction'

    def form_feedback(self, cr, uid, data, acquirer_name, context=None):
        invalid_parameters, tx = None, None
        tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
        if hasattr(self, tx_find_method_name):
            tx = getattr(self, tx_find_method_name)(cr, uid, data, context=context)

        invalid_param_method_name = '_%s_form_get_invalid_parameters' % acquirer_name
        if hasattr(self, invalid_param_method_name):
            invalid_parameters = getattr(self, invalid_param_method_name)(cr, uid, tx, data, context=context)

        if invalid_parameters:
            _error_message = '%s: incorrect tx data:\n' % (acquirer_name)
            for item in invalid_parameters:
                _error_message += '\t%s: received %s instead of %s\n' % (item[0], item[1], item[2])
            _logger.error(_error_message)
            return False

        feedback_method_name = '_%s_form_validate' % acquirer_name
        if hasattr(self, feedback_method_name):
            res = getattr(self, feedback_method_name)(cr, uid, tx, data, context=context)
        if res:
            if tx.state == 'done':
                acquirer_journal = tx.acquirer_id.journal_id
                amount = tx.amount
                booking_reference = tx.reference
                partner_id = tx.partner_id
                self.create_payment_voucher(cr, uid, acquirer_journal, booking_reference, partner_id, amount, context=context)
                return True
        return True

    def create_payment_voucher(self,cr, uid, acquirer_journal, booking_reference, partner_id, amount,context=None):
        voucher_obj = self.pool['account.voucher']
        booking_reference_id = self.pool['hotel.book'].search(cr, uid, [('name', '=', booking_reference)])
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        if booking_reference_id:
            voucher_data = {
                'partner_id': partner_id.id,
                'amount': amount,
                'journal_id': acquirer_journal.id,
                'book_reference_id': booking_reference_id[0],
                'account_id': acquirer_journal.default_debit_account_id.id,
                'company_id': company_id,
                'type': 'receipt'
            }
            hotel_voucher = voucher_obj.create(cr, uid, voucher_data, context)
            hotel_voucher = voucher_obj.browse(cr, uid, hotel_voucher, context)
            hotel_voucher.button_proforma_voucher()


class Hotel_book(osv.Model):
    _inherit = "hotel.book"

    _columns = {
        'payment_acquirer_id': fields.many2one('payment.acquirer', 'Payment Acquirer', on_delete='set null'),
        'payment_tx_id': fields.many2one('payment.transaction', 'Transaction', on_delete='set null'),
    }


class payment_transaction(osv.Model):
    _inherit = 'payment.transaction'

    _columns = {
        # link with the sale order
        'hotel_order_id': fields.many2one('hotel.book', 'Hotel Book'),
    }