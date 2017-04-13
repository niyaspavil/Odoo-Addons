from openerp import SUPERUSER_ID
from openerp.addons.web.controllers.main import Home
from openerp.addons.website_event.controllers.main import website_event
from openerp.addons.web.controllers.main import ensure_db
from datetime import datetime, timedelta as td
from openerp.addons.web import http
from openerp.http import request
import logging
from passlib.context import CryptContext
import openerp
from openerp.tools.translate import _

import werkzeug.urls
from dateutil.relativedelta import relativedelta
from openerp import tools

_logger = logging.getLogger(__name__)

default_crypt_context = CryptContext(
    ['pbkdf2_sha512', 'md5_crypt'],
    deprecated=['md5_crypt'],
)


############ Code for Event Registration ################


class web_event_register(website_event):
    @http.route(['/event', '/event/page/<int:page>'], type='http', auth="public", website=True)
    def events(self, page=1, **searches):
        cr, uid, context = request.cr, request.uid, request.context
        hotel_obj = request.registry.get('hotel.book')
        user_obj = request.registry.get('res.users')
        user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
        partner_id = user_id.partner_id.id
        hotel_rec = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('state', '=', 'draft')])
        if hotel_rec:
            return request.redirect('/cart/confirmation/' + str(hotel_rec[0]))
        event_obj = request.registry['event.event']
        type_obj = request.registry['event.type']
        country_obj = request.registry['res.country']

        searches.setdefault('date', 'all')
        searches.setdefault('type', 'all')
        searches.setdefault('country', 'all')

        domain_search = {}

        def sdn(date):
            return date.strftime('%Y-%m-%d 23:59:59')

        def sd(date):
            return date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        today = datetime.today()
        dates = [
            ['all', _('Next Events'), [("date_end", ">", sd(today))], 0],
            ['today', _('Today'), [
                ("date_end", ">", sd(today)),
                ("date_begin", "<", sdn(today))],
             0],
            ['week', _('This Week'), [
                ("date_end", ">=", sd(today + relativedelta(days=-today.weekday()))),
                ("date_begin", "<", sdn(today + relativedelta(days=6 - today.weekday())))],
             0],
            ['nextweek', _('Next Week'), [
                ("date_end", ">=", sd(today + relativedelta(days=7 - today.weekday()))),
                ("date_begin", "<", sdn(today + relativedelta(days=13 - today.weekday())))],
             0],
            ['month', _('This month'), [
                ("date_end", ">=", sd(today.replace(day=1))),
                ("date_begin", "<", (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00'))],
             0],
            ['nextmonth', _('Next month'), [
                ("date_end", ">=", sd(today.replace(day=1) + relativedelta(months=1))),
                ("date_begin", "<", (today.replace(day=1) + relativedelta(months=2)).strftime('%Y-%m-%d 00:00:00'))],
             0],
            ['old', _('Old Events'), [
                ("date_end", "<", today.strftime('%Y-%m-%d 00:00:00'))],
             0],
        ]

        # search domains
        current_date = None
        current_type = None
        current_country = None
        for date in dates:
            if searches["date"] == date[0]:
                domain_search["date"] = date[2]
                if date[0] != 'all':
                    current_date = date[1]
        if searches["type"] != 'all':
            current_type = type_obj.browse(cr, uid, int(searches['type']), context=context)
            domain_search["type"] = [("type", "=", int(searches["type"]))]

        if searches["country"] != 'all' and searches["country"] != 'online':
            current_country = country_obj.browse(cr, uid, int(searches['country']), context=context)
            domain_search["country"] = ['|', ("country_id", "=", int(searches["country"])), ("country_id", "=", False)]
        elif searches["country"] == 'online':
            domain_search["country"] = [("country_id", "=", False)]

        # ---------------------------------------------------------------

        manager_group = user_obj.has_group(cr, uid, 'event.group_event_manager')
        if manager_group == False:
            domain_search["published"] = [("website_published", "=", True)]

        # ----------------------------------------------------------------

        def dom_without(without):
            domain = [('state', "in", ['draft', 'confirm', 'done'])]
            for key, search in domain_search.items():
                if key != without:
                    domain += search
            return domain

        # count by domains without self search
        for date in dates:
            if date[0] <> 'old':
                date[3] = event_obj.search(
                    request.cr, request.uid, dom_without('date') + date[2],
                    count=True, context=request.context)

        domain = dom_without('type')
        types = event_obj.read_group(
            request.cr, request.uid, domain, ["id", "type"], groupby="type",
            orderby="type", context=request.context)
        type_count = event_obj.search(request.cr, request.uid, domain,
                                      count=True, context=request.context)
        types.insert(0, {
            'type_count': type_count,
            'type': ("all", _("All Categories"))
        })

        domain = dom_without('country')
        countries = event_obj.read_group(
            request.cr, request.uid, domain, ["id", "country_id"],
            groupby="country_id", orderby="country_id", context=request.context)
        country_id_count = event_obj.search(request.cr, request.uid, domain,
                                            count=True, context=request.context)
        countries.insert(0, {
            'country_id_count': country_id_count,
            'country_id': ("all", _("All Countries"))
        })

        step = 10  # Number of events per page
        event_count = event_obj.search(
            request.cr, request.uid, dom_without("none"), count=True,
            context=request.context)
        pager = request.website.pager(
            url="/event",
            url_args={'date': searches.get('date'), 'type': searches.get('type'), 'country': searches.get('country')},
            total=event_count,
            page=page,
            step=step,
            scope=5)

        order = 'website_published desc, date_begin'
        if searches.get('date', 'all') == 'old':
            order = 'website_published desc, date_begin desc'
        obj_ids = event_obj.search(
            request.cr, request.uid, dom_without("none"), limit=step,
            offset=pager['offset'], order=order, context=request.context)
        events_ids = event_obj.browse(request.cr, request.uid, obj_ids,
                                      context=request.context)

        values = {
            'current_date': current_date,
            'current_country': current_country,
            'current_type': current_type,
            'event_ids': events_ids,
            'dates': dates,
            'types': types,
            'countries': countries,
            'pager': pager,
            'searches': searches,
            'search_path': "?%s" % werkzeug.url_encode(searches),
        }

        return request.website.render("website_event.index", values)

    @http.route(['/event/<model("event.event"):event>/register'], type='http', auth="public", website=True)
    def event_register(self, event, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_obj = registry.get('res.partner')
        user_obj = registry.get('res.users')
        event_obj = registry.get('event.event')
        user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
        price_list = partner_obj.browse(cr, SUPERUSER_ID, user_id.partner_id.id, context)
        event_ids = event_obj.browse(cr, SUPERUSER_ID, event.id, context)
        pricelist = []
        for i in event_ids:
            for j in i.event_ticket_ids:
                price = registry.get('product.pricelist').price_get(cr, SUPERUSER_ID,
                                                                    [price_list.property_product_pricelist.id],
                                                                    j.product_id.id, 1.0, price_list.id, {
                                                                        'uom': j.product_id.uom_id.id,
                                                                    })[price_list.property_product_pricelist.id]
                pricelist.append(price)
        values = {
            'event': event_ids,
            'pricelist': pricelist,
            'main_object': event,
            'range': range,
            'partner': price_list
        }

        return request.website.render("website_event.event_description_full", values)

    @http.route(['/event/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, event_id, **post):

        cr, uid, context = request.cr, request.uid, request.context
        ticket_obj = request.registry.get('event.event.ticket')
        partner_obj = request.registry.get('res.partner')
        user_obj = request.registry.get('res.users')
        hotel_obj = request.registry.get('hotel.book')
        hotel_vals = {}
        order_lines = []

        login_id = request.httpsession.get('login')

        if login_id == None:
            return request.redirect('/web/login')
        else:
            ticket_id = int(post.get('ticket_id'))
            user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
            addr = partner_obj.address_get(cr, uid, [user_id.partner_id.id], ['delivery', 'invoice', 'contact'])
            partner_id = user_id.partner_id.id
            pricelist_id = user_id.property_product_pricelist.id
            partner_invoice_id = addr['invoice']
            partner_shipping_id = addr['delivery']
            ticket = ticket_obj.browse(cr, SUPERUSER_ID, ticket_id, context=context)
            rsrv_from = datetime.strptime(ticket.event_id.date_begin, '%Y-%m-%d %H:%M:%S').date()
            rsrv_to = datetime.strptime(ticket.event_id.date_end, '%Y-%m-%d %H:%M:%S').date()
            order_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
            hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('is_pay', '=', False)])
            hotel_partner = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context)
            if not hotel_partner:
                hotel_vals = {

                    'partner_id': partner_id,
                    'pricelist_id': pricelist_id,
                    'partner_invoice_id': partner_invoice_id,
                    'partner_shipping_id': partner_shipping_id,
                    'order_date': order_date,
                    'rsrv_from': rsrv_from,
                    'rsrv_to': rsrv_to,
                }
                if hotel_vals:
                    price = request.registry.get('product.pricelist').price_get(cr, SUPERUSER_ID,
                                                                                [pricelist_id],
                                                                                ticket.product_id.id, 1.0, partner_id, {
                                                                                    'uom': ticket.product_id.uom_id.id,
                                                                                })[pricelist_id]
                    order_lines.append((0, 0, {
                        'event_name': ticket.event_id.id,
                        'ticket_type': ticket.id,
                        'seat_available': ticket.seat_available,
                        'price': price
                    }))
                    hotel_vals.update({'event_tab': order_lines})
                hotel_id = hotel_obj.create(cr, SUPERUSER_ID, hotel_vals, context)
                request.session['book_order_id'] = hotel_id
                return request.redirect('/cart/confirmation/%s' % hotel_id)
            else:
                price = request.registry.get('product.pricelist').price_get(cr, SUPERUSER_ID,
                                                                            [pricelist_id],
                                                                            ticket.product_id.id, 1.0, partner_id, {
                                                                                'uom': ticket.product_id.uom_id.id,
                                                                            })[pricelist_id]

                order_lines.append((0, 0, {
                    'event_name': ticket.event_id.id,
                    'ticket_type': ticket.id,
                    'seat_available': ticket.seat_available,
                    'price': price
                }))
                hotel_vals.update({'event_tab': order_lines})
                hotel_id = hotel_obj.write(cr, SUPERUSER_ID, hotel_partner.id, hotel_vals, context)
                request.session['book_order_id'] = hotel_partner.id
                return request.redirect('/cart/confirmation/%s' % hotel_partner.id)

    @http.route(['/hotel/list/<int:book_id>'], type='http', auth="public", website=True)
    def event_list(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        event_obj = request.env['hotel.events']
        hotel_obj = request.env['hotel.book']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')

        if login_id == None:
            return request.redirect('/web/login')
        else:
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            book_ids = hotel_obj.sudo().search([('id', '=', int(book_id)), ('is_pay', '=', False)])

            if partner_id == book_ids.partner_id.id:
                event_ids = event_obj.sudo().search([('book_id', '=', int(book_id))])

                values = {
                    'event_ids': event_ids,
                    'book_ids': book_ids
                }
                return request.website.render('website_hotel_book.event_list', values)

    @http.route(['/hotel/delete'], type='json', auth="public", methods=['POST'], website=True)
    def event_delete(self, book_id, event_id, ticket_id, display=True):

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            order = request.website.hotel_get_order(book_id=book_id)
            value = order._eventdelete(book_id=book_id, event_id=event_id, ticket_id=ticket_id)

            values = {
                'book_id': int(book_id)
            }
            return values


############ Code for Event Registration ################


############ Code for Accommodation Booking ################

class web_acoomodation_register(http.Controller):
    def get_pricelist(self):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        partner = pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
        pricelist = partner.property_product_pricelist
        if pricelist:
            return pricelist

    def accommodation_values(self, book_id, data=None):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        categ_obj = registry.get('product.category')
        hotel_obj = request.env['hotel.book']

        hotel_ids = hotel_obj.sudo().search([('id', '=', int(book_id))])

        category_ids = categ_obj.search(cr, SUPERUSER_ID, [('is_accom_type', '=', 1),('available_in_web', '=', 1)], context=context)
        categories = categ_obj.browse(cr, SUPERUSER_ID, category_ids, context)
        from_date = datetime.strptime(hotel_ids.rsrv_from, '%Y-%m-%d')
        from_date = from_date - td(days=1)
        to_date = datetime.strptime(hotel_ids.rsrv_to, '%Y-%m-%d')

        from_date = from_date.strftime('%m/%d/%Y')
        to_date = to_date.strftime('%m/%d/%Y')
        register = {
            'from_date': from_date,
            'to_date': to_date,
            'accom_type': False
        }
        if data:
            register = data

        values = {
            'categories': categories,
            'register': register,
            'vacant_rooms': {},
            'error': {},
            'book_id': book_id
        }
        return values

    mandatory_billing_fields = ["from_date", "to_date", "accom_type"]
    mandatory_shipping_fields = ["from_date", "to_date", "accom_type"]

    def accommodation_form_validate(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        # Validation
        error = dict()
        for field_name in self.mandatory_billing_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        return error

    @http.route(['/accommodation/type'], type='json', auth="public", methods=['POST'], website=True)
    def accommodation_type_check(self, from_date, to_date, accom_type, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        value = dict()
        date_list = []
        vacant_list = []
        categ_obj = request.registry.get('product.category')
        room_obj = request.env['product.product']
        hotel_obj = request.env['hotel.accommodation']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            room_ids = room_obj.sudo().search(
                [('categ_id', '=', int(accom_type))])  ## Select All Rooms form product.product

            category = categ_obj.browse(request.cr, SUPERUSER_ID, int(accom_type), context).id
            category_ids = categ_obj.search(cr, SUPERUSER_ID, [('is_accom_type', '=', 1),('available_in_web', '=', 1)], context=context)
            categories = categ_obj.browse(cr, SUPERUSER_ID, category_ids, context)  ## Select Accommodation Type

            date1 = datetime.strptime(from_date, '%m/%d/%Y')
            date2 = datetime.strptime(to_date, '%m/%d/%Y')
            delta = date2 - date1
            for i in range(delta.days + 1):
                date = date1 + td(days=i)
                date = date.strftime('%Y-%m-%d')
                date_list.append(date)
                room_list = []
                for record in room_ids:
                    rooms_ids = hotel_obj.sudo().search([('bed_type', '=', record.id), ('status', '=', 'occupied'),
                                                         ('accom_type', '=', int(accom_type)),
                                                         ('accom_date', '=', date)])  # Find Occupaid Rooms
                    if not rooms_ids:
                        room_list.append((record.id, record.name, self.room_cost_check(record.id)['list_price']))
                vacant_list.append(room_list)
            value['date_list'] = date_list
            value['category_id'] = category
            value['categories'] = [(cat.id, cat.name) for cat in categories]
            value['room_id'] = vacant_list
            return value

    @http.route(['/rooms/type'], type='json', auth="public", methods=['POST'], website=True)
    def room_type_check(self, line_date, type_id, display=True):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        room_list = []
        data = dict()
        room_obj = request.env['product.product']
        hotel_obj = request.env['hotel.accommodation']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            room_ids = room_obj.sudo().search(
                [('categ_id', '=', int(type_id))])  ## Select All Rooms form product.product
            for record in room_ids:
                rooms_ids = hotel_obj.sudo().search(
                    [('bed_type', '=', record.id), ('status', '=', 'occupied'), ('accom_type', '=', int(type_id)),
                     ('accom_date', '=', line_date)])  # Find Occupaid Rooms
                if not rooms_ids:
                    room_list.append((record.id, record.name, self.room_cost_check(record.id)['list_price']))
            data['rooms'] = room_list
            return data

    @http.route(['/rooms/cost'], type='json', auth="public", methods=['POST'], website=True)
    def room_cost_check(self, room_id, display=True):

        data = dict()
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        room_obj = request.env['product.product']

        template_obj = pool['product.template']
        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            pricelist = self.get_pricelist()

            temp_id = room_obj.sudo().search([('id', '=', int(room_id))]).product_tmpl_id.id
            image_small = room_obj.sudo().search([('id', '=', int(room_id))]).image_small

            if not context.get('pricelist'):
                context['pricelist'] = int(self.get_pricelist())
            product = template_obj.browse(cr, uid, temp_id, context=context)

            data['list_price'] = product.price
            data['image_small'] = image_small
            return data

    @http.route(['/accommodation'], type='http', auth="public", website=True)
    def accommodation_register(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        user_obj = request.registry.get('res.users')
        hotel_obj = request.registry.get('hotel.book')

        login_id = request.httpsession.get('login')

        if login_id == None:
            return request.redirect('/web/login')
        else:
            user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
            partner_id = user_id.partner_id.id

            hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('is_pay', '=', False)])
            book_id = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context).id

            values = self.accommodation_values(book_id, post)
            return request.website.render('website_hotel_book.accommodation', values)

    @http.route(['/accommodation/validate'], type='json', auth="public", methods=['POST'], website=True)
    def accomodation_validate(self, book_id, from_date, to_date, accom_type, data1, type1, room1, cost1, display=True):
        cr, uid, context = request.cr, request.uid, request.context
        hotel_obj = request.env['hotel.book']
        hotel_vals = {}
        order_lines = []
        data = dict()
        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            hotel_ids = hotel_obj.sudo().browse(int(book_id))
            date1 = datetime.strptime(from_date, '%m/%d/%Y')
            date2 = datetime.strptime(to_date, '%m/%d/%Y')
            rsrv_from = date1.strftime('%Y-%m-%d')
            rsrv_to = date2.strftime('%Y-%m-%d')

            hotel_vals = {

                'rsrv_from': rsrv_from,
                'rsrv_to': rsrv_to,
                'is_accom': True,
                'accom_typ': int(accom_type),
            }
            i = 0
            while i < len(data1):
                order_lines.append((0, 0, {
                    'book_id': int(book_id),
                    'accom_date': data1[i],
                    'accom_type': type1[i],
                    'bed_type': room1[i],
                    'cost': cost1[i]
                }))
                i = i + 1

            hotel_vals.update({'accom_tab': order_lines})
            hotel_id = hotel_ids.sudo().write(hotel_vals)
            request.session['book_order_id'] = book_id
            data['book_id'] = book_id
            return data

    @http.route(['/hotel/rooms/<int:book_id>'], type='http', auth="public", website=True)
    def room_list(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        room_obj = request.env['hotel.accommodation']
        hotel_obj = request.env['hotel.book']
        categ_obj = request.env['product.category']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            book_ids = hotel_obj.sudo().search([('id', '=', int(book_id)), ('is_pay', '=', False)])
            if partner_id == book_ids.partner_id.id:
                room_ids = room_obj.sudo().search([('book_id', '=', int(book_id))])

                from_date = datetime.strptime(book_ids.rsrv_from, '%Y-%m-%d')
                to_date = datetime.strptime(book_ids.rsrv_to, '%Y-%m-%d')

                from_date = from_date.strftime('%m/%d/%Y')
                to_date = to_date.strftime('%m/%d/%Y')

                categ_ids = categ_obj.sudo().search([('is_accom_type', '=', 1),('available_in_web', '=', 1)])

                values = {
                    'room_ids': room_ids,
                    'book_ids': book_ids,
                    'categories': categ_ids,
                    'from_date': from_date,
                    'to_date': to_date
                }
                return request.website.render('website_hotel_book.room_list', values)

    @http.route(['/room/change'], type='json', auth="public", methods=['POST'], website=True)
    def room_change(self, line_date, accom_id, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        room_list = []
        data = dict()

        room_obj = request.env['product.product']
        hotel_obj = request.env['hotel.accommodation']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            room_ids = room_obj.sudo().search(
                [('categ_id', '=', int(accom_id))])  ## Select All Rooms form product.product

            for record in room_ids:
                rooms_ids = hotel_obj.sudo().search(
                    [('bed_type', '=', record.id), ('status', '=', 'occupied'), ('accom_type', '=', int(accom_id)),
                     ('accom_date', '=', line_date)])  # Find Occupaid Rooms
                if not rooms_ids:
                    room_list.append((record.id, record.name))
            data['rooms'] = room_list
            return data

    @http.route(['/room/edit'], type='json', auth="public", methods=['POST'], website=True)
    def room_edit(self, book_id, old_roomid, line_date, cur_id, accom_id, room_id, cost, display=True):

        room_obj = request.env['hotel.accommodation']
        sum_obj = request.env['hotel.accommodationsummery']
        hotel_obj = request.env['hotel.book']
        categ_obj = request.env['product.category']

        value = dict()
        categ_ids = categ_obj.sudo().search([('id', '=', int(accom_id))])

        hotel_ids = hotel_obj.sudo().search([('id', '=', int(book_id))])
        newroom_ids = False
        oldroom_ids = sum_obj.sudo().search([('reservation_id', '=', int(book_id)), (
        'product_id', '=', int(old_roomid))])  ## Old Sumery data and reduce quatity by One
        if oldroom_ids:
            change = oldroom_ids.sudo().write({'product_uom_qty': oldroom_ids.product_uom_qty - 1})
            if oldroom_ids.product_uom_qty == 0:
                oldroom_ids.sudo().unlink()
        if room_id:
            newroom_ids = sum_obj.sudo().search(
                [('reservation_id', '=', int(book_id)), ('product_id', '=', int(room_id))])

            if newroom_ids:
                newroom_ids.sudo().write(
                    {'product_uom_qty': newroom_ids.product_uom_qty + 1})  ## Add new item within Summery
            else:
                new = sum_obj.sudo().create({
                    'product_id': int(room_id),
                    'product_uom_qty': 1,
                    'name': categ_ids.name,
                    'price_unit': float(cost),
                    'pricelist_id': hotel_ids.pricelist_id.id,
                    'reservation_id': int(book_id)
                })

                room_ids = room_obj.sudo().search([('id', '=', int(cur_id))])
                status = room_ids.sudo().write(
                    {'accom_type': int(accom_id), 'bed_type': int(room_id), 'cost': float(cost)})
                if status:
                    value['cur_id'] = int(cur_id)
        else:
            room_ids = room_obj.sudo().search([('id', '=', int(cur_id))])
            room_ids.sudo().unlink()
        return value


############ Code for Accommodation Booking ################

########### Code for Booking Services & Amenities #################

class website_service_booking(http.Controller):
    def get_pricelist(self):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        partner = pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
        pricelist = partner.property_product_pricelist
        if pricelist:
            return pricelist

    def service_values(self, book_id, data=None):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        hotel_obj = request.env['hotel.book']

        hotel_ids = hotel_obj.sudo().search([('id', '=', int(book_id))])
        values = {
            'rsrv_from': hotel_ids.rsrv_from,
            'rsrv_to': hotel_ids.rsrv_to,
            'book_id': book_id
        }
        return values

    @http.route(['/hotelservice'], type='http', auth="public", website=True)
    def service_register(self, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_obj = request.registry.get('res.users')
        hotel_obj = request.registry.get('hotel.book')

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
            partner_id = user_id.partner_id.id

            hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('is_pay', '=', False)])
            book_id = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context).id

            values = self.service_values(book_id, post)
            return request.website.render('website_hotel_book.service', values)

    @http.route(['/service/type'], type='json', auth="public", methods=['POST'], website=True)
    def service_type_check(self, rsrv_from, rsrv_to, display=True):

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        value = dict()
        service_list = []
        amenity_list = []
        service_obj = request.env['hotel.services']
        amenity_obj = request.env['hotel.amenities']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            service_ids = service_obj.sudo().search([('status', '=', 'available')])
            amenity_ids = amenity_obj.sudo().search([('status', '=', 'available')])
            template_obj = pool['product.product']

            pricelist = self.get_pricelist()

            if not context.get('pricelist'):
                context['pricelist'] = int(self.get_pricelist())
                for srvc in service_ids:
                    service = template_obj.browse(cr, uid, int(srvc.product_id.id), context=context)
                    service_list.append(service)
                for amnt in amenity_ids:
                    amenity = template_obj.browse(cr, uid, int(amnt.product_id.id), context=context)
                    amenity_list.append(amenity)

            if amenity_list or service_list:
                value['service_ids'] = [(srvc.id, srvc.name, srvc.product_tmpl_id.price) for srvc in service_list]
                value['amenity_ids'] = [(amnt.id, amnt.name, amnt.product_tmpl_id.price) for amnt in amenity_list]
                return value

    @http.route(['/service/validate'], type='json', auth="public", methods=['POST'], website=True)
    def service_validate(self, book_id, rsrv_from, rsrv_to, service, scost, amenity, acost, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        hotel_obj = request.env['hotel.book']
        service_obj = request.env['hotel.services']
        amenity_obj = request.env['hotel.amenities']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            hotel_vals = {}
            order_lines1 = []
            order_lines2 = []
            data = dict()
            hotel_ids = hotel_obj.sudo().browse(int(book_id))

            i = 0
            while i < len(service):
                if service[i]:
                    service_id = service_obj.sudo().search([('product_id', '=', int(service[i]))]).id
                    order_lines1.append((0, 0, {
                        'book_id': int(book_id),
                        'service_name': int(service_id),
                        'price': float(scost[i]),
                    }))
                i = i + 1

            j = 0
            while j < len(amenity):
                if amenity[j]:
                    amenity_id = amenity_obj.sudo().search([('product_id', '=', int(amenity[j]))]).id
                    order_lines2.append((0, 0, {
                        'book_id': int(book_id),
                        'amenities_name': int(amenity_id),
                        'price': float(acost[j]),
                    }))
                j = j + 1

            hotel_vals.update({'service_tab': order_lines1, 'amenity_tab': order_lines2})
            hotel_id = hotel_ids.sudo().write(hotel_vals)
            request.session['book_order_id'] = book_id
            data['book_id'] = book_id
            return data

    @http.route(['/hotel/service/<int:book_id>'], type='http', auth="public", website=True)
    def service_list(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        service_obj = request.env['hotel.bookservice']
        hotel_obj = request.env['hotel.book']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            book_ids = hotel_obj.sudo().search([('id', '=', int(book_id)), ('is_pay', '=', False)])
            if partner_id == book_ids.partner_id.id:
                service_ids = service_obj.sudo().search([('book_id', '=', int(book_id))])

                values = {
                    'service_ids': service_ids,
                    'book_ids': book_ids
                }
                return request.website.render('website_hotel_book.service_list', values)

    @http.route(['/service/delete'], type='json', auth="public", methods=['POST'], website=True)
    def service_delete(self, book_id, srvs_id, curent_id, display=True):

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            order = request.website.hotel_get_order(book_id=book_id)
            value = order._servicedelete(book_id=book_id, srvs_id=srvs_id, curent_id=curent_id)

            values = {
                'book_id': int(book_id)
            }
            return values

    @http.route(['/hotel/aminity/<int:book_id>'], type='http', auth="public", website=True)
    def amenity_list(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        aminity_obj = request.env['hotel.amenitiesbook']
        hotel_obj = request.env['hotel.book']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            book_ids = hotel_obj.sudo().search([('id', '=', int(book_id)), ('is_pay', '=', False)])
            if partner_id == book_ids.partner_id.id:
                aminity_ids = aminity_obj.sudo().search([('book_id', '=', int(book_id))])
                values = {
                    'aminity_ids': aminity_ids,
                    'book_ids': book_ids
                }
                return request.website.render('website_hotel_book.aminity_list', values)

    @http.route(['/aminity/delete'], type='json', auth="public", methods=['POST'], website=True)
    def amenity_delete(self, book_id, aminity_id, curent_id, display=True):

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            order = request.website.hotel_get_order(book_id=book_id)
            value = order._aminitydelete(book_id=book_id, aminity_id=aminity_id, curent_id=curent_id)

            values = {
                'book_id': int(book_id)
            }
            return values


########### Code for Booking Services & Amenities #################

############ Code for Meals Booking ################

class website_meals_booking(http.Controller):
    def meals_values(self, book_id, data=None):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        hotel_obj = request.env['hotel.book']

        hotel_ids = hotel_obj.sudo().search([('id', '=', int(book_id))])
        values = {

            'rsrv_from': hotel_ids.rsrv_from,
            'rsrv_to': hotel_ids.rsrv_to,
            'book_id': book_id
        }
        return values

    @http.route(['/hotelmeals'], type='http', auth="public", website=True)
    def meals_register(self, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        user_obj = request.registry.get('res.users')
        hotel_obj = request.registry.get('hotel.book')

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
            partner_id = user_id.partner_id.id

            hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('is_pay', '=', False)])
            book_id = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context).id

            values = self.meals_values(book_id, post)
            return request.website.render('website_hotel_book.meals', values)

    @http.route(['/meals/type'], type='json', auth="public", methods=['POST'], website=True)
    def meals_type_check(self, rsrv_from, rsrv_to, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        value = dict()
        date_list = []

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            date1 = datetime.strptime(rsrv_from, '%Y-%m-%d')
            date2 = datetime.strptime(rsrv_to, '%Y-%m-%d')

            first_date = date1.strftime('%Y-%m-%d')
            lat_date = date2.strftime('%Y-%m-%d')

            delta = date2 - date1
            for i in range(delta.days + 1):
                date = date1 + td(days=i)
                date = date.strftime('%Y-%m-%d')
                date_list.append(date)
            value['date_list'] = date_list
            return value

    @http.route(['/meals/validate'], type='json', auth="public", methods=['POST'], website=True)
    def meals_validate(self, book_id, rsrv_from, rsrv_to, data1, fast1, lunch1, dinner1, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            hotel_obj = request.env['hotel.book']
            hotel_vals = {}
            order_lines = []
            data = dict()
            hotel_ids = hotel_obj.sudo().browse(int(book_id))

            hotel_vals = {
                'is_meal': True,
                'is_break': True,
                'is_lunch': True,
                'is_dinner': True
            }
            i = 0
            while i < len(data1):
                order_lines.append((0, 0, {
                    'book_id': int(book_id),
                    'meals_date': data1[i],
                    'breakfast': fast1[i],
                    'lunch': lunch1[i],
                    'dinner': dinner1[i]
                }))
                i = i + 1

            hotel_vals.update({'meals_tab': order_lines})
            hotel_id = hotel_ids.sudo().write(hotel_vals)
            request.session['book_order_id'] = book_id
            data['book_id'] = book_id
            return data

    @http.route(['/hotel/meals/<int:book_id>'], type='http', auth="public", website=True)
    def meals_list(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        meals_obj = request.env['hotel.meals']
        hotel_obj = request.env['hotel.book']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            book_ids = hotel_obj.sudo().search([('id', '=', int(book_id)), ('is_pay', '=', False)])
            if partner_id == book_ids.partner_id.id:
                meals_ids = meals_obj.sudo().search([('book_id', '=', int(book_id))])

                values = {
                    'meals_ids': meals_ids,
                    'book_ids': book_ids,
                }
                return request.website.render('website_hotel_book.meals_list', values)

    @http.route(['/meals/edit'], type='json', auth="public", methods=['POST'], website=True)
    def meals_edit(self, book_id, line_date, cur_id, fast_check, lnch_check, diner_check, display=True):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        meals_obj = request.env['hotel.meals']
        sum_obj = request.env['hotel.mealssummery']
        mobject = request.env['hotel.meal']
        hotel_obj = request.env['hotel.book']
        value = dict()

        bproduct_id = False
        lproduct_id = False
        dproduct_id = False
        brfst = False
        lnch = False
        dnnr = False

        hotel_ids = hotel_obj.sudo().search([('id', '=', int(book_id))])
        order = request.website.hotel_get_order(book_id=book_id)

        qty = 1

        mid = mobject.sudo().search([])
        for rec in mid:
            if rec.is_types == 1:
                bproduct_id = rec.product_id.id
                brfst = order._meals_pricelist(hotel_ids=hotel_ids, rec=rec)
            elif rec.is_types == 3:
                lproduct_id = rec.product_id.id
                lnch = order._meals_pricelist(hotel_ids=hotel_ids, rec=rec)
            elif rec.is_types == 2:
                dproduct_id = rec.product_id.id
                dnnr = order._meals_pricelist(hotel_ids=hotel_ids, rec=rec)

        bsum_ids = sum_obj.sudo().search(
            ([('reservation_id', '=', int(book_id)), ('product_id', '=', int(bproduct_id))]))
        lsum_ids = sum_obj.sudo().search(
            ([('reservation_id', '=', int(book_id)), ('product_id', '=', int(lproduct_id))]))
        dsum_ids = sum_obj.sudo().search(
            ([('reservation_id', '=', int(book_id)), ('product_id', '=', int(dproduct_id))]))

        meals_ids = meals_obj.sudo().search([('id', '=', int(cur_id))])

        if fast_check:
            if bsum_ids:  ## Adding or Update quantity to Meals summery
                if meals_ids.breakfast == False:
                    bsum_ids.sudo().write({'product_uom_qty': bsum_ids.product_uom_qty + 1})
            else:
                sum_obj.sudo().create({
                    'product_id': int(bproduct_id),
                    'product_uom_qty': 1,
                    'name': 'Meals',
                    'price_unit': float(brfst),
                    'pricelist_id': hotel_ids.pricelist_id.id,
                    'reservation_id': int(book_id)
                })
        else:
            if bsum_ids:
                bsum_ids.sudo().write({'product_uom_qty': bsum_ids.product_uom_qty - 1})

        if lnch_check:
            if lsum_ids:
                if meals_ids.lunch == False:
                    lsum_ids.sudo().write({'product_uom_qty': lsum_ids.product_uom_qty + 1})
            else:
                sum_obj.sudo().create({
                    'product_id': int(bproduct_id),
                    'product_uom_qty': 1,
                    'name': 'Meals',
                    'price_unit': float(brfst),
                    'pricelist_id': hotel_ids.pricelist_id.id,
                    'reservation_id': int(book_id)
                })
        else:
            if lsum_ids:
                lsum_ids.sudo().write({'product_uom_qty': lsum_ids.product_uom_qty - 1})

        if diner_check:
            if dsum_ids:
                if meals_ids.dinner == False:
                    dsum_ids.sudo().write({'product_uom_qty': dsum_ids.product_uom_qty + 1})
            else:
                sum_obj.sudo().create({
                    'product_id': int(bproduct_id),
                    'product_uom_qty': 1,
                    'name': 'Meals',
                    'price_unit': float(brfst),
                    'pricelist_id': hotel_ids.pricelist_id.id,
                    'reservation_id': int(book_id)
                })
        else:
            if dsum_ids:
                dsum_ids.sudo().write({'product_uom_qty': dsum_ids.product_uom_qty - 1})

        status = meals_ids.sudo().write({'breakfast': fast_check, 'lunch': lnch_check, 'dinner': diner_check})
        if status:
            value['cur_id'] = int(cur_id)
            return value


############ Code for Meals Booking ################



################ Code for Reservation cart ################

class website_cart(http.Controller):
    @http.route(['/cart/confirmation/<int:book_id>'], type='http', auth="public", website=True)
    def cart_register(self, book_id, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        hotel_obj = request.registry.get('hotel.book')
        event_obj = request.registry.get('hotel.eventsummery')
        accom_obj = request.env['hotel.accommodationsummery']
        meals_obj = request.env['hotel.mealssummery']
        service_obj = request.env['hotel.servicesummery']
        amenity_obj = request.env['hotel.amenitiesummery']
        product_obj = request.env['product.product']
        users_obj = request.env['res.users']

        login_id = request.httpsession.get('login')

        if login_id == None:
            return request.redirect('/web/login')
        else:
            if book_id:
                hotel_id = book_id
            else:
                hotel_id = request.httpsession.get('book_order_id')
            partner_id = users_obj.sudo().search([('id', '=', int(uid))]).partner_id.id

            hotel_ids = hotel_obj.search(cr, SUPERUSER_ID, [('id', '=', int(hotel_id))])
            book_id = hotel_obj.browse(cr, SUPERUSER_ID, hotel_ids, context)
            prservice_obj = request.env['hotel.services']
            pramenity_obj = request.env['hotel.amenities']
            if partner_id == book_id.partner_id.id:
                evnt_ids = event_obj.search(cr, SUPERUSER_ID, [('reservation_id', '=', int(hotel_id))])
                event_id = event_obj.browse(cr, SUPERUSER_ID, evnt_ids, context)

                meals_ids = meals_obj.sudo().search([('reservation_id', '=', int(hotel_id))])
                accom_ids = accom_obj.sudo().search([('reservation_id', '=', int(hotel_id))])

                service_ids = service_obj.sudo().search([('reservation_id', '=', int(hotel_id))])
                amenity_ids = amenity_obj.sudo().search([('reservation_id', '=', int(hotel_id))])

                prservice_ids = prservice_obj.sudo().search([('status', '=', 'available')])
                pramenity_ids = pramenity_obj.sudo().search([('status', '=', 'available')])

                values = {
                    'new_id': False,
                    'book_id': book_id,
                    'event_ids': event_id,
                    'accom_ids': accom_ids,
                    'meals_ids': meals_ids,
                    'service_ids': service_ids,
                    'amenity_ids': amenity_ids,
                    'prservice_ids': prservice_ids,
                    'pramenity_ids': pramenity_ids
                }
                return request.website.render("website_hotel_book.hotel_cart", values)

    @http.route(['/reservation/change'], type='http', auth="public", website=True)
    def reservation_delete(self, **post):

        login_id = request.httpsession.get('login')
        values = False
        if login_id == None:
            return request.redirect('/web/login')
        else:
            if post:
                book_id = post.get('hotel_id')
                order = request.website.hotel_get_order(book_id=book_id)
                value = order._resrvationcancel(book_id=book_id)
                values = {
                    'new_id': True,
                    'book_id': False,
                    'event_ids': False,
                    'accom_ids': False,
                    'meals_ids': False,
                    'service_ids': False,
                    'amenity_ids': False,
                    'prservice_ids': False,
                    'pramenity_ids': False
                }
        return request.website.render("website_hotel_book.hotel_cart", values)


################## Code for Reservation cart ##################

################## Code for Reservation and Payment View ###################

class website_reservation(http.Controller):
    def sale_get_transaction(self, reference=False):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        transaction_obj = request.registry.get('payment.transaction')
        tx_id = request.session.get('sale_transaction_id')
        if tx_id:
            tx_ids = transaction_obj.search(cr, SUPERUSER_ID, [('id', '=', tx_id), ('state', 'not in', ['cancel'])],
                                            context=context)
            if tx_ids:
                return transaction_obj.browse(cr, SUPERUSER_ID, tx_ids[0], context=context)
            else:
                request.session['sale_transaction_id'] = False
        trans = transaction_obj.search(cr, SUPERUSER_ID, [('reference', '=', reference)])
        if trans:
            return transaction_obj.browse(cr, SUPERUSER_ID, trans[0], context=context)
        return False

    def sale_reset(self):
        request.session.update({
            'hotel_order_id': False,
            'sale_transaction_id': False,
            'sale_order_code_pricelist_id': False,
        })

    @http.route(['/reserve/views'], type='http', auth="public", website=True)
    def event_register(self, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        user_obj = request.env['res.users']
        hotel_obj = request.env['hotel.book']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            user_ids = user_obj.sudo().search([('login', '=', login_id)])
            hotel_ids = hotel_obj.sudo().search([('partner_id', '=', user_ids.partner_id.id)])
            values = {
                'login_id': login_id,
                'hotel_ids': hotel_ids
            }

            return request.website.render("website_hotel_book.booking_line", values)

    @http.route(['/hotel/payment/<int:hotel_id>'], type='http', auth="public", website=True)
    def payment(self, hotel_id, **post):

        cr, uid, context = request.cr, request.uid, request.context
        payment_obj = request.registry.get('payment.acquirer')
        hotel_obj = request.env['hotel.book']
        advance_obj = request.env['hotel.advance']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            advance = advance_obj.sudo().search([('is_active', '=', True)])

            book = hotel_obj.sudo().search([('id', '=', int(hotel_id))])

            shipping_partner_id = False
            if book:
                if book.partner_shipping_id.id:
                    shipping_partner_id = book.partner_shipping_id.id
                else:
                    shipping_partner_id = book.partner_invoice_id.id

            values = {
                'book': book,
                'advance': advance
            }
            acquirer_ids = payment_obj.search(cr, SUPERUSER_ID, [('website_published', '=', True),
                                                                 ('company_id', '=', book.partner_id.company_id.id)],
                                              context=context)
            values['acquirers'] = list(payment_obj.browse(cr, uid, acquirer_ids, context=context))

            render_ctx = dict(context, submit_class='btn btn-primary', submit_txt=_('Pay Now'))
            for acquirer in values['acquirers']:
                acquirer.button = payment_obj.render(
                    cr, SUPERUSER_ID, acquirer.id,
                    book.name,
                    advance.advance_pay,
                    book.pricelist_id.currency_id.id,
                    partner_id=shipping_partner_id,
                    tx_values={
                        'return_url': '/hotel/payment/validate/%s' % hotel_id,
                    },
                    context=render_ctx)

            return request.website.render("website_hotel_book.payment_view", values)

    @http.route(['/hotel/payment/transaction'], type='json', auth="public", website=True)
    def payment_transaction(self, book_id, acquirer_id, display=True):

        cr, uid, context = request.cr, request.uid, request.context
        transaction_obj = request.registry.get('payment.transaction')
        hotel_obj = request.env['hotel.book']
        advance_obj = request.env['hotel.advance']

        advance = advance_obj.sudo().search([('is_active', '=', True)])

        book = hotel_obj.sudo().search([('id', '=', int(book_id))])

        hotel_ids = hotel_obj.sudo().browse(int(book_id))

        if not book or acquirer_id is None:
            return request.redirect("/event")

        assert book.partner_id.id != request.website.partner_id.id

        # find an already existing transaction
        tx = self.sale_get_transaction(hotel_ids.name)
        if tx:
            if tx.state == 'draft':  # button cliked but no more info -> rewrite on tx or create a new one ?
                tx.write({
                    'acquirer_id': acquirer_id,
                })
            tx_id = tx.id
        else:
            tx_id = transaction_obj.create(cr, SUPERUSER_ID, {
                'acquirer_id': acquirer_id,
                'type': 'form',
                'amount': advance.advance_pay,
                'currency_id': book.pricelist_id.currency_id.id,
                'partner_id': book.partner_id.id,
                'partner_country_id': book.partner_id.country_id.id,
                'reference': book.name,
                'hotel_order_id': book.id,
            }, context=context)
            request.session['sale_transaction_id'] = tx_id

        # update quotation
        hotel_ids.sudo().write({
            'payment_acquirer_id': acquirer_id,
            'payment_tx_id': request.session['sale_transaction_id']
        })
        # confirm the quotation
        return tx_id

    @http.route('/shop/payment/get_status/<int:hotel_order_id>', type='json', auth="public", website=True)
    def payment_get_status(self, hotel_order_id, **post):
        cr, uid, context = request.cr, request.uid, request.context

        order = request.registry['hotel.book'].browse(cr, SUPERUSER_ID, hotel_order_id, context=context)
        if not order:
            return {
                'state': 'error',
                'message': '<p>%s</p>' % _('There seems to be an error with your request.'),
            }

        tx_ids = request.registry['payment.transaction'].search(cr, SUPERUSER_ID, [('reference', '=', order.name)],
                                                                context=context)
        if not tx_ids:
            if order.amount_total:
                return {
                    'state': 'error',
                    'message': '<p>%s</p>' % _('There seems to be an error with your request.'),
                }
            else:
                state = 'done'
                message = ""
                validation = None
        else:
            tx = request.registry['payment.transaction'].browse(cr, SUPERUSER_ID, tx_ids[0], context=context)
            state = tx.state
            if state == 'done':
                order.write({'is_pay': True, 'state': 'pre_reserved'})
                message = '<p>%s</p>' % _('Your payment has been received.')
            elif state == 'cancel':
                message = '<p>%s</p>' % _('The payment seems to have been canceled.')
            elif state == 'pending' and tx.acquirer_id.validation == 'manual':
                message = '<p>%s</p>' % _('Your transaction is waiting confirmation.')
                if tx.acquirer_id.post_msg:
                    message += tx.acquirer_id.post_msg
            else:
                message = '<p>%s</p>' % _('Your transaction is waiting confirmation.')
            validation = tx.acquirer_id.validation
        return {
            'state': state,
            'message': message,
            'validation': validation
        }

    @http.route('/hotel/payment/validate/<int:book_id>', type='http', auth="public", website=True)
    def payment_validate(self, book_id, transaction_id=None, **post):

        cr, uid, context = request.cr, request.uid, request.context
        email_act = None
        hotel_obj = request.env['hotel.book']
        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            if transaction_id is None:
                tx = self.sale_get_transaction()
            else:
                tx = request.registry['payment.transaction'].browse(cr, uid, transaction_id, context=context)

            book = hotel_obj.sudo().search([('id', '=', int(book_id))])

            if not tx or not book:
                return request.redirect('/event')

            if email_act and email_act.get('context'):
                composer_values = {}
                email_ctx = email_act['context']
                public_id = request.website.user_id.id
                if uid == public_id:
                    composer_values['email_from'] = request.website.user_id.company_id.email
                composer_id = request.registry['mail.compose.message'].create(cr, SUPERUSER_ID, composer_values,
                                                                              context=email_ctx)
                request.registry['mail.compose.message'].send_mail(cr, SUPERUSER_ID, [composer_id], context=email_ctx)

            self.sale_reset()
            if tx.state == 'done':
                return request.redirect('/hotel/confirmation/%s' % book_id)
            else:
                # tx.unlink()
                return request.redirect('/hotel/cancel/%s' % book_id)

    @http.route(['/hotel/confirmation/<int:book_id>'], type='http', auth="public", website=True)
    def payment_confirmation(self, book_id, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        cr, uid, context = request.cr, request.uid, request.context

        hotel_obj = request.env['hotel.book']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            if book_id:
                book = hotel_obj.sudo().search([('id', '=', int(book_id))])
            else:
                return request.redirect('/event')

            return request.website.render("website_hotel_book.confirmation", {'book': book})

    @http.route(['/hotel/cancel/<int:book_id>'], type='http', auth="public", website=True)
    def payment_cancel(self, book_id, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        cr, uid, context = request.cr, request.uid, request.context

        hotel_obj = request.env['hotel.book']

        login_id = request.httpsession.get('login')
        if login_id == None:
            return request.redirect('/web/login')
        else:
            if book_id:
                book = hotel_obj.sudo().search([('id', '=', int(book_id))])
            else:
                return request.redirect('/event')

            return request.website.render("website_hotel_book.cancel", {'book': book})


################## Code for Reservation View  and Payment View###################


################## Code for Customer Registration and Login###################

class customer_register(Home):
    def register_values(self, data=None):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        orm_country = registry.get('res.country')
        state_orm = registry.get('res.country.state')
        event_orm = registry.get('event.event')

        now = datetime.now().date()
        event_list = []
        obj_ids = event_orm.search(cr, uid, [], context=context)
        for events_ids in event_orm.browse(cr, uid, obj_ids, context=context):
            date1 = datetime.strptime(events_ids.date_begin, '%Y-%m-%d %H:%M:%S').date()
            if date1 >= now:
                event_list.append(events_ids.id)

        event_ids = event_orm.browse(cr, uid, event_list, context=context)

        country_ids = orm_country.search(cr, SUPERUSER_ID, [], context=context)
        countries = orm_country.browse(cr, SUPERUSER_ID, country_ids, context)
        states_ids = state_orm.search(cr, SUPERUSER_ID, [], context=context)
        states = state_orm.browse(cr, SUPERUSER_ID, states_ids, context)
        register = {}
        if data:
            register = data

        # Default search by user country
        country_code = request.session['geoip'].get('country_code')
        if country_code:
            country_ids = request.registry.get('res.country').search(cr, uid, [('code', '=', country_code)],
                                                                     context=context)
            if country_ids:
                register['country_id'] = country_ids[0]

        values = {
            'countries': countries,
            'states': states,
            'register': register,
            'event_ids': event_ids,
            'error': {},
            'email_val': {},
        }
        return values

    mandatory_billing_fields = ["name", "phone", "email", "street", "city", "country_id", "zip", "pwd", "security_id",
                                "answer"]
    optional_billing_fields = ["street2", "state_id"]
    mandatory_shipping_fields = ["name", "phone", "street", "city", "country_id", "zip", "security_id", "answer"]
    optional_shipping_fields = ["state_id"]

    def _crypt_context(self, cr, uid, id, context=None):
        return default_crypt_context

    def register_form_validate(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        # Validation
        error = dict()
        for field_name in self.mandatory_billing_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        return error

    def email_form_validate(self, data):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        # Validation
        email_val = dict()
        partner_obj = registry.get('res.partner')
        email = data.get('email')
        email_ids = partner_obj.search(cr, SUPERUSER_ID, [('email', '=', email)], context=context)
        values = []
        if email_ids:
            # key_expires = datetime.today() + datetime.timedelta(2)
            email_val['email'] = 'exist'
        return email_val

    @http.route('/web/login', type='http', website=True, auth="public")
    def web_login(self, redirect=None, **kw):

        ensure_db()
        users_obj = request.registry.get('res.users')
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)
        if not request.uid:
            request.uid = openerp.SUPERUSER_ID
        values = request.params.copy()
        if not redirect:
            redirect = '/web?' + request.httprequest.query_string
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except openerp.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if uid is not False:
                is_customer = users_obj.browse(request.cr, request.uid, uid, request.context).partner_id.customer
                if is_customer:
                    redirect = '/event'
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = "Wrong login/password"
        return request.render('web.login', values)

    @http.route(['/register'], type='http', auth="public", website=True)
    def registre(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        values = self.register_values(post)
        return request.website.render("website_hotel_book.register", values)

    @http.route(['/confirm'], type='http', auth="public", website=True)
    def confirm(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        valu = {

            'confirm': False,
        }
        return request.website.render("website_hotel_book.confirm", valu)

    @http.route(['/register/confirm'], type='http', auth="public", website=True)
    def confirm_regitration(self, redirect=None, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        partner_vals = {}
        users_vals = {}
        lang = request.context.get('lang')
        partner_obj = registry.get('res.partner')
        users_obj = registry.get('res.users')
        values = self.register_values(post)
        values["error"] = self.register_form_validate(values["register"])
        values["email_val"] = self.email_form_validate(values["register"])
        if values["email_val"]:
            if values["error"]:
                return request.website.render("website_hotel_book.register", values)
            else:
                return request.website.render("website_hotel_book.register", values)
        else:
            encrypted = self._crypt_context(cr, uid, id, context=context).encrypt(post.get('pwd'))

            users_vals = {

                'name': post.get('name'),
                'active': True,
                'login': post.get('email'),
                'password': post.get('pwd'),
                'password_crypt': encrypted,
                'security_id': post.get('security_id'),
                'sec_answer': post.get('answer'),
                'lang': lang

            }
            users_id = users_obj.create(cr, SUPERUSER_ID, users_vals, context=context)

            partner_id = users_obj.browse(cr, SUPERUSER_ID, users_id, context=context).partner_id.id

            partner_vals = {

                'name': post.get('name'),
                'dob': False,
                'street': post.get('street'),
                'street2': post.get('street2'),
                'city': post.get('city'),
                'zip': post.get('zip'),
                'country_id': post.get('country_id'),
                'state_id': post.get('state_id'),
                'phone': post.get('phone'),
                'email': post.get('email'),
                'customer': True,
                'doc_type': False,
                'doc_val': False,
                'doc_date': False,
                'lang': lang
            }
            partner_id = partner_obj.write(cr, SUPERUSER_ID, [partner_id], partner_vals, context=context)
            data = {}
            values = self.register_values(data)

            return request.redirect('/web/login')

    def forgot_values(self, data=None):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        register = dict()

        if data:
            register = data

        values = {

            'forgot': False,
            'register': register,
            'error': {},
            'email_val': {},
            'security_val': {},
            'answer_val': {}
        }
        return values

    @http.route(['/forgot'], type='http', auth="public", website=True)
    def confirm(self, **post):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        values = self.forgot_values(post)
        return request.website.render("website_hotel_book.customer_forgot", values)

    @http.route(['/forgot/confirm'], type='http', auth="public", website=True)
    def forgot_confirm(self, **post):

        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        user_obj = request.registry.get('res.users')
        email_val = dict()
        security_val = dict()
        error = dict()
        answer_val = dict()
        values = self.forgot_values(post)

        email = post.get('email')
        security = post.get('security_id')
        answer = post.get('answer')
        encrypted = self._crypt_context(cr, uid, id, context=context).encrypt(post.get('pwd'))

        email_ids = user_obj.search(request.cr, SUPERUSER_ID, [('login', '=', email)])  ## Checking of valid Email_ID
        user_id = user_obj.browse(request.cr, SUPERUSER_ID, email_ids, request.context).id
        email_id = user_obj.browse(request.cr, SUPERUSER_ID, email_ids, request.context).login
        security_id = user_obj.browse(request.cr, SUPERUSER_ID, email_ids, request.context).security_id
        sec_answer = user_obj.browse(request.cr, SUPERUSER_ID, email_ids, request.context).sec_answer

        if not email_id:
            email_val['email'] = 'Invalid E-mail ID'
            values["email_val"] = email_val

        if security_id.id != security:
            security_val['security'] = 'Incorrect Security Question'
            values["security_val"] = security_val

        if sec_answer != answer:
            answer_val['answer'] = 'Incorrect Answer'
            values["answer_val"] = answer_val

        for field_name in self.mandatory_billing_fields:
            if not post.get(field_name):  ## Checking of Mandotary field correctly set
                error[field_name] = 'missing'
                values["error"] = error

        if values["answer_val"] and values["security_val"] and values["security_val"] and values["error"]:
            return request.website.render("website_hotel_book.customer_forgot", values)
        else:
            users_vals = {

                'password': post.get('pwd'),
                'password_crypt': encrypted,

            }
            user_ids = user_obj.write(request.cr, SUPERUSER_ID, user_id, users_vals, request.context)
            values['forgot'] = True
            values['register'] = {}
            values['security_val'] = {}
            return request.website.render("website_hotel_book.customer_forgot", values)


        ################## Code for Customer Registration and Login ###################

    @http.route(['/hotel/timer'], type='json', auth="public", website=True)
    def get_timer(self):
        cr, uid, context = request.cr, request.uid, request.context
        hotel_obj = request.registry.get('hotel.book')
        user_obj = request.registry.get('res.users')
        user_id = user_obj.browse(cr, SUPERUSER_ID, uid, context)
        login_id = request.httpsession.get('login')
        partner_id = user_id.partner_id.id
        hotel_rec = hotel_obj.search(cr, SUPERUSER_ID, [('partner_id', '=', partner_id), ('state', '=', 'draft')])
        if hotel_rec and login_id:
            write_date = hotel_obj.browse(cr, SUPERUSER_ID, hotel_rec[0], context).create_date
            now = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
            write_date_datetime = datetime.strptime(write_date, '%Y-%m-%d %H:%M:%S')
            diff = now - write_date_datetime
            return {'time': int(diff.seconds), 'hotel_id': hotel_rec[0]}
        return {'time': 0, 'hotel_id': False}
