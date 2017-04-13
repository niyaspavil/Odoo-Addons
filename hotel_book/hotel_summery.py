from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp import models, fields as new_field, api, _
from openerp.exceptions import except_orm, Warning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

import datetime
import time
from dateutil.relativedelta import relativedelta


## Code for Preparing Summery ##
class hotel_accommodationsummery(osv.osv):
    _name = 'hotel.accommodationsummery'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id)
            cur = line.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {

        'product_id': fields.many2one('product.product', 'Rooms', ),
        'name': fields.text('Accommodation Type'),
        'product_uom_qty': fields.integer('Quantity', ),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, readonly=True,
                                        help="Pricelist for current reservation. "),
        'tax_id': fields.many2many('account.tax', 'hotel_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),

    }


class hotel_mealssummery(osv.osv):
    _name = 'hotel.mealssummery'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id)
            cur = line.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {

        'product_id': fields.many2one('product.product', 'Meals', ),
        'name': fields.text('Description'),
        'product_uom_qty': fields.integer('Quantity', ),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, readonly=True,
                                        help="Pricelist for current reservation. "),
        'tax_id': fields.many2many('account.tax', 'hotel_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),

    }


class hotel_eventsummery(osv.osv):
    _name = 'hotel.eventsummery'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id)
            cur = line.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {

        'product_id': fields.many2one('product.product', 'Events', ),
        'name': fields.text('Ticket Types'),
        'product_uom_qty': fields.integer('Quantity', ),
        'hotel_event_id': fields.integer('event id'),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, readonly=True,
                                        help="Pricelist for current reservation. "),
        'tax_id': fields.many2many('account.tax', 'hotel_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),

    }


class hotel_servicesummery(osv.osv):
    _name = 'hotel.servicesummery'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id)
            cur = line.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {

        'product_id': fields.many2one('product.product', 'Services', ),
        'name': fields.text('Description'),
        'product_uom_qty': fields.integer('Quantity', ),
        'hotel_service_id': fields.integer('service id'),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, readonly=True,
                                        help="Pricelist for current reservation. "),
        'tax_id': fields.many2many('account.tax', 'hotel_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),

    }


class hotel_amenitiesummery(osv.osv):
    _name = 'hotel.amenitiesummery'

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):

        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id)
            cur = line.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {

        'product_id': fields.many2one('product.product', 'Amenities', ),
        'name': fields.text('Description'),
        'hotel_amenity_id': fields.integer('amenity id'),
        'product_uom_qty': fields.integer('Quantity', ),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', readonly=True,
                                        help="Pricelist for current reservation. "),
        'tax_id': fields.many2many('account.tax', 'hotel_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
        'reservation_id': fields.many2one('hotel.book', 'Reservation Id', ondelete='cascade'),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),

    }