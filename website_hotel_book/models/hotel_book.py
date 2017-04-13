import random

from openerp import SUPERUSER_ID
from openerp.osv import osv, orm, fields


class hotel_book(osv.Model):
    _inherit = "hotel.book"

    _columns = {
        'payment_acquirer_id': fields.many2one('payment.acquirer', 'Payment Acquirer', on_delete='set null'),
        'payment_tx_id': fields.many2one('payment.transaction', 'Transaction', on_delete='set null'),
    }

    def _eventdelete(self, cr, uid, ids, book_id=None, event_id=None, ticket_id=0, context=None, **kwargs):


        hotel_obje = self.pool.get('hotel.events')
        event_obj = self.pool.get('hotel.eventsummery')
        event_reg_obj = self.pool.get('event.registration')
        ticket_obj = self.pool.get('event.event.ticket')

        quantity = 0

        ticket_ids = ticket_obj.search(cr, SUPERUSER_ID, [('id', '=', int(ticket_id)), ('event_id', '=', int(event_id))], context=context)
        ticket_record = ticket_obj.browse(cr, SUPERUSER_ID, ticket_ids, context=context)

        evnt_ids = hotel_obje.search(cr, SUPERUSER_ID, [('book_id', '=', int(book_id)), ('event_name', '=', int(event_id)), ('ticket_type', '=', int(ticket_id))], context=context)
        if type(evnt_ids) == list:
            evnt_ids = evnt_ids[0]
        evnt_record = hotel_obje.browse(cr, SUPERUSER_ID, evnt_ids, context=context)
        regis_ids = event_reg_obj.search(cr, SUPERUSER_ID, [('reservation_id', '=', int(book_id)), ('event_id', '=', int(event_id)), ('event_ticket_id', '=', int(ticket_id))], context=context)
        resgs_record = event_reg_obj.browse(cr, SUPERUSER_ID, regis_ids, context=context)
        event_ids = event_obj.search(cr, SUPERUSER_ID, [('reservation_id', '=', int(book_id)), ('product_id', '=', evnt_record.ticket_type.product_id.id), ('name', '=', evnt_record.ticket_type.name)])
        event_record = event_obj.browse(cr, SUPERUSER_ID, event_ids, context=context)
        sum_id = 0
        if event_record:
            if len(event_record) > 1:
                event_record = event_record[0]
            sum_id = event_obj.unlink(cr, SUPERUSER_ID, [event_record.id], context=context)
        regis_id = 0
        if resgs_record:
            if len(resgs_record) > 1:
                resgs_record = resgs_record[0]
            regis_id = event_reg_obj.unlink(cr, SUPERUSER_ID, [resgs_record.id], context=context)

        seat_id = ticket_obj.write(cr, SUPERUSER_ID, [ticket_record.id], {'seat_available': ticket_record.seat_available+1}, context=context)

        link_id = hotel_obje.unlink(cr, SUPERUSER_ID, [evnt_record.id], context=context)

        if sum_id and regis_id and seat_id and link_id:
            return {'quantity': quantity}

    def _servicedelete(self, cr, uid, ids, book_id=None, srvs_id=None, curent_id=None, context=None, **kwargs):

        service_obje = self.pool.get('hotel.bookservice')
        sumry_obj = self.pool.get('hotel.servicesummery')

        service_ids = service_obje.search(cr, SUPERUSER_ID, [('book_id', '=', int(book_id)), ('service_name', '=', int(srvs_id))], context=context)
        service_record = service_obje.browse(cr, SUPERUSER_ID, service_ids, context=context)

        for record in service_record:
            sumery_ids = sumry_obj.search(cr, SUPERUSER_ID, [('reservation_id', '=', int(book_id)), ('product_id', '=', record.service_name.product_id.id)])
            sumery_record = sumry_obj.browse(cr, SUPERUSER_ID, sumery_ids, context=context)
            if sumery_record:
                sum_id = sumry_obj.unlink(cr, SUPERUSER_ID, [sumery_record.id], context=context)

            link_id = service_obje.unlink(cr, SUPERUSER_ID, [record.id], context=context)

        if sum_id and link_id:
            return True

    def _aminitydelete(self, cr, uid, ids, book_id=None, aminity_id=None, curent_id=None, context=None, **kwargs):

        aminity_obje = self.pool.get('hotel.amenitiesbook')
        sumry_obj = self.pool.get('hotel.amenitiesummery')

        aminity_ids = aminity_obje.search(cr, SUPERUSER_ID, [('book_id', '=', int(book_id)), ('amenities_name', '=', int(aminity_id))], context=context)
        aminity_record = aminity_obje.browse(cr, SUPERUSER_ID, aminity_ids, context=context)

        for record in aminity_record:
            sumery_ids = sumry_obj.search(cr, SUPERUSER_ID, [('reservation_id', '=', int(book_id)), ('product_id', '=', record.amenities_name.product_id.id)])
            sumery_record = sumry_obj.browse(cr, SUPERUSER_ID, sumery_ids, context=context)
            if sumery_record:
                sum_id = sumry_obj.unlink(cr, SUPERUSER_ID, [sumery_record.id], context=context)

            link_id = aminity_obje.unlink(cr, SUPERUSER_ID, [record.id], context=context)

        if sum_id and link_id:
            return True

    def _resrvationcancel(self, cr, uid, ids, book_id=None, context=None, **kwargs):

        hotel_obj = self.pool.get('hotel.book')
        ticket_obj = self.pool.get('event.event.ticket')
        link_id = False
        value = dict()

        hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('id', '=', int(book_id))], context=context)
        hotel_record = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context=context)

        if hotel_record.event_tab:
            for record in hotel_record.event_tab:
                ticket = ticket_obj.write(cr, SUPERUSER_ID, [record.ticket_type.id], {'seat_available': record.ticket_type.seat_available+1}, context=context)

        for rec in hotel_record:
            value['name'] = rec.name
            link_id = hotel_obj.unlink(cr, SUPERUSER_ID, [rec.id], context=context)

        if link_id:
            return value

    def _meals_pricelist(self, cr, uid, ids, hotel_ids=None, rec=None, context=None, **kwargs):

        qty = 1
        if rec.is_types == 1:
            brfst = self.pool.get('product.pricelist').price_get(cr, uid, [hotel_ids.pricelist_id.id],
                    rec.product_id.id , qty or 1.0, hotel_ids.partner_id.id, {
                        'uom': rec.product_id.uom_id.id,
                        'date': hotel_ids.order_date,
                    })[hotel_ids.pricelist_id.id]
            return brfst
        elif rec.is_types == 3:
            lnch = self.pool.get('product.pricelist').price_get(cr, uid, [hotel_ids.pricelist_id.id],
                    rec.product_id.id , qty or 1.0, hotel_ids.partner_id.id, {
                        'uom': rec.product_id.uom_id.id,
                        'date': hotel_ids.order_date,
                    })[hotel_ids.pricelist_id.id]
            return lnch
        elif rec.is_types == 2:
            dnnr = self.pool.get('product.pricelist').price_get(cr, uid, [hotel_ids.pricelist_id.id],
                    rec.product_id.id , qty or 1.0, hotel_ids.partner_id.id, {
                        'uom': rec.product_id.uom_id.id,
                        'date': hotel_ids.order_date,
                    })[hotel_ids.pricelist_id.id]
            return dnnr


class website(orm.Model):

    _inherit = 'website'

    def hotel_get_order(self, cr, uid, ids, book_id=False, context=None):

        hotele_obj = self.pool['hotel.book']

        hotel_ids = hotele_obj.search(cr, SUPERUSER_ID, [('id', '=', int(book_id))], context=context)
        book_order = hotele_obj.browse(cr, SUPERUSER_ID, hotel_ids, context=context)
        return book_order

    def sale_product_domain(self, cr, uid, ids, context=None):
        # remove product event from the website content grid and list view (not removed in detail view)
        return ['&'] + super(website, self).sale_product_domain(cr, uid, ids, context=context) + [('website_published', '=', True)]
