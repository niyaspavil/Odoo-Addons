from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import api
from openerp import netsvc

## Code for Creating Sale Order ##
import time


class hotel_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {

        'reservation_id': fields.many2one('hotel.book', 'Reservation Id'),
        'reference_id': fields.char('Reference Number', )
    }

    _defaults = {

        'picking_policy': 'direct',
        'order_policy': 'manual',
    }

    # def create(self, cr, uid, values, context=None):
    #
    #     res = super(hotel_order, self).create(cr, uid, values, context=context)
    #     folio_obj = self.pool.get('hotel.folio')
    #     if 'reservation_id' in values:
    #         order_vals = {
    #             'order_id': res,
    #         }
    #         folio_obj.create(cr, uid, order_vals, context=context)
    #
    #     return res


class hotel_folio(osv.osv):
    _name = 'hotel.folio'

    _inherits = {'sale.order': 'order_id'}

    _columns = {

        'order_id': fields.many2one('sale.order', 'Order_id', required=True, select=True, ondelete='cascade'),
        'folio_number': fields.char('Folio Number', readonly=True),
        'room_lines': fields.one2many('hotel.folio.line', 'folio_id', readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                      help="Hotel room reservation detail."),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id'),
        'reference_id': fields.char('Reference Number', )
    }

    _defaults = {

        'folio_number': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.folio'),
    }

    def action_wait(self, cr, uid, ids, *args):
        sale_order_obj = self.pool.get('sale.order')
        res = False
        for o in self.browse(cr, uid, ids):
            res = sale_order_obj.action_wait(cr, uid, [o.order_id.id], *args)
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write(cr, uid, [o.id], {'state': 'manual'})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress'})
        return res

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done']):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        invoice_id = self.pool.get('sale.order').action_invoice_create(cr, uid, order_ids, grouped=False,
                                                                       states=['confirmed', 'done'])
        return invoice_id

    def action_view_invoice(self, cr, uid, ids, context=None):

        sale_order_obj = self.pool.get('sale.order')
        res = False
        for o in self.browse(cr, uid, ids):
            res = sale_order_obj.action_view_invoice(cr, uid, [o.order_id.id], context=context)
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        sale_order_obj = self.pool.get('sale.order')
        hotel_book_obj = self.pool.get('hotel.book')
        res = False
        for o in self.browse(cr, uid, ids):
            if o.order_id.invoice_ids:
                invoice_id = o.order_id.invoice_ids
                if invoice_id.state == 'draft':
                    cr.execute("update account_invoice set state='cancel' where id=%s", (invoice_id.id,))
                if invoice_id.state == 'paid' or invoice_id.state == 'open':
                    raise osv.except_osv(_('Error!'), _(
                        'You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
            res = sale_order_obj.action_cancel(cr, uid, [o.order_id.id], context=context)
            hotel_book_obj.write(cr, uid, o.reservation_id.id, {'state': 'pre_reserved'})
        print "folioooooooo"
        print self.write(cr, uid, ids, {'state': 'cancel'})
        return res

    def copy_quotation(self, cr, uid, ids, context=None):

        sale_order_obj = self.pool.get('sale.order')
        res = False
        for o in self.browse(cr, uid, ids):
            res = sale_order_obj.copy_quotation(cr, uid, [o.order_id.id], context=context)
        return res

    def button_dummy(self, cr, uid, ids, context=None):
        return True


class hotel_registration(osv.osv):
    _inherit = 'event.registration'

    _columns = {

        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
    }


class hotel_event(osv.osv):
    _inherit = 'event.event.ticket'

    _columns = {

        'seat_available': fields.integer('Availability')
    }

    def create(self, cr, uid, values, context=None):
        if values.get('seats_max'):
            values.update({'seat_available': values['seats_max']})
        return super(hotel_event, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        res = super(hotel_event, self).write(cr, uid, ids, values, context=context)
        if 'seats_max' in values:
            self.write(cr, uid, ids, {'seat_available': values['seats_max']}, context=context)
        return res


class hotel_folio_line(osv.Model):
    def copy(self, cr, uid, id, default=None, context=None):
        return self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context=context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)

    def _number_packages(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'
    _inherits = {'sale.order.line': 'order_line_id'}
    _columns = {
        'order_line_id': fields.many2one('sale.order.line', 'Order Line', required=True, ondelete='cascade'),
        'folio_id': fields.many2one('hotel.folio', 'Folio', ondelete='cascade'),

    }

    def create(self, cr, uid, vals, context=None, check=True):
        if 'folio_id' in vals:
            print 'Value: ', vals
            print 'Folio: ', vals['folio_id']
            folio = self.pool.get("hotel.folio").browse(cr, uid, vals['folio_id'], context=context)
            vals.update({'order_id': folio.order_id.id})
            print 'ORDER: ', folio.order_id.id
        return super(osv.Model, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_line_id:
                sale_line_obj.unlink(cr, uid, [line.order_line_id.id], context=context)
        return super(hotel_folio_line, self).unlink(cr, uid, ids, context=None)

    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').uos_change(cr, uid, line_ids, product_uos, product_uos_qty=0,
                                                           product_id=None)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').product_id_change(cr, uid, line_ids, pricelist, product, qty=0,
                                                                  uom=False, qty_uos=0, uos=False, name='',
                                                                  partner_id=partner_id,
                                                                  lang=False, update_tax=True, date_order=False)

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
                           uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                           lang=False, update_tax=True, date_order=False):
        return self.product_id_change(cursor, user, ids, pricelist, product, qty=0,
                                      uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                                      lang=False, update_tax=True, date_order=False)

    def button_confirm(self, cr, uid, ids, context=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').button_confirm(cr, uid, line_ids, context=context)

    def button_done(self, cr, uid, ids, context=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        res = self.pool.get('sale.order.line').button_done(cr, uid, line_ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        res = self.write(cr, uid, ids, {'state': 'done'})
        for line in self.browse(cr, uid, ids, context):
            wf_service.trg_write(uid, 'sale.order', line.order_line_id.order_id.id, cr)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        line_id = self.browse(cr, uid, id).order_line_id.id
        return self.pool.get('sale.order.line').copy_data(cr, uid, line_id, default=None, context=context)
