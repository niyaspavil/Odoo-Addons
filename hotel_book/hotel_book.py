from openerp.osv import osv, fields, orm
from openerp import models
from openerp import api
from openerp.tools.translate import _
from datetime import datetime, timedelta as td
from datetime import date
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID


############################ Code for Hotel Booking ####################
class hotel_book(osv.osv):
    _name = 'hotel.book'
    _order = 'name desc'

    def copy(self, cr, uid, id, default={}, context=None):
        self.pool.get('event.registration').search(cr, uid, [])
        res = super(hotel_book, self).copy(cr, uid, id, default=default, context=context)
        hotel_obj = self.pool.get('hotel.book')
        hotel_rec = hotel_obj.browse(cr, uid, res, context)
        hotel_rec.check_changeaccom()
        default = {} if default is None else default.copy()
        default['meals_sum'] = False
        return res

    def _get_order_accom(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hotel.accommodation').browse(cr, uid, ids, context=context):
            result[line.book_id.id] = True
        return result.keys()

    def _get_order_meals(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hotel.meals').browse(cr, uid, ids, context=context):
            result[line.book_id.id] = True
        return result.keys()

    def _get_order_events(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hotel.events').browse(cr, uid, ids, context=context):
            result[line.book_id.id] = True
        return result.keys()

    def _get_order_service(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hotel.bookservice').browse(cr, uid, ids, context=context):
            result[line.book_id.id] = True
        return result.keys()

    def _get_order_amenities(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hotel.amenitiesbook').browse(cr, uid, ids, context=context):
            result[line.book_id.id] = True
        return result.keys()

    def _portal_payment_block(self, cr, uid, ids, fieldname, arg, context=None):
        result = dict.fromkeys(ids, False)
        payment_acquirer = self.pool['payment.acquirer']
        for this in self.browse(cr, SUPERUSER_ID, ids, context=context):
            # if this.state not in ('draft', 'cancel') and not this.invoiced:
            result[this.id] = payment_acquirer.render_payment_block(
                cr, uid, this.name, this.amount_total, this.pricelist_id.currency_id.id,
                partner_id=this.partner_id.id, company_id=this.company_id.id, context=context)
        return result

    @api.model
    def _default_company(self):
        return self.env.user.company_id.id

    @api.one
    @api.depends('amount_total')
    def _compute_total_amount(self):
        self.balance_amount = self.amount_total - self.advance_amount

    @api.one
    @api.depends('meals_sum', 'accom_sum', 'events_sum', 'service_sum', 'amenity_sum')
    def _compute_total_amount1(self):
        for order in self:
            brkid = 0.0
            lnchid = 0.0
            dnnrid = 0.0
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0
            res = {}
            tax_obj = self.pool.get('account.tax')
            cur_obj = self.pool.get('res.currency')
            mid = self.pool.get('hotel.meal').search(self._cr, self._uid, [], context=self._context)
            hotel_ids = self.browse(order.id)
            if mid or (bool(hotel_ids.meals_tab) == False):

                pricelist = hotel_ids.pricelist_id.id
                partner_id = hotel_ids.partner_id.id
                order_date = hotel_ids.order_date
                qty = 1

                for meals in self.pool.get('hotel.meal').browse(self._cr, self._uid, mid, context=self._context):

                    if meals.is_types == 1:
                        brfst = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                                                                             meals.product_id.id, qty or 1.0,
                                                                             partner_id, {
                                                                                 'uom': meals.product_id.uom_id.id,
                                                                                 'date': order_date,
                                                                             })[pricelist]
                        brkid = meals.product_id.id
                        btax = meals.product_id.taxes_id

                    elif meals.is_types == 3:

                        lnch = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                                                                            meals.product_id.id, qty or 1.0, partner_id,
                                                                            {
                                                                                'uom': meals.product_id.uom_id.id,
                                                                                'date': order_date,
                                                                            })[pricelist]
                        lnchid = meals.product_id.id
                        ltax = meals.product_id.taxes_id

                    elif meals.is_types == 2:
                        dnnr = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                                                                            meals.product_id.id, qty or 1.0, partner_id,
                                                                            {
                                                                                'uom': meals.product_id.uom_id.id,
                                                                                'date': order_date,
                                                                            })[pricelist]
                        dnnrid = meals.product_id.id
                        dtax = meals.product_id.taxes_id

                for record in self.browse(self.ids):
                    res[record.id] = {
                        'amount_untaxed': 0.0,
                        'amount_tax': 0.0,
                        'amount_total': 0.0,
                    }
                    bid = self.pool.get('hotel.meals').search(self._cr, self._uid,
                                                              [('breakfast', '=', True), ('book_id', '=', record.id)])
                    lid = self.pool.get('hotel.meals').search(self._cr, self._uid,
                                                              [('lunch', '=', True), ('book_id', '=', record.id)])
                    did = self.pool.get('hotel.meals').search(self._cr, self._uid,
                                                              [('dinner', '=', True), ('book_id', '=', record.id)])
                    cur = record.pricelist_id.currency_id
                    for line in record.accom_tab:
                        if line.bed_type:
                            amount_untaxed = amount_untaxed + line.cost
                            for c in tax_obj.compute_all(self._cr, self._uid, line.bed_type.taxes_id, line.cost, 1,
                                                         line.bed_type.id)['taxes']:
                                amount_tax += c.get('amount', 0.0)

                    if len(bid) != 0:
                        if brkid:
                            amount_untaxed = amount_untaxed + (len(bid) * brfst)
                            for c in tax_obj.compute_all(self._cr, self._uid, btax, brfst, len(bid), brkid)['taxes']:
                                amount_tax += c.get('amount', 0.0)
                        else:
                            raise osv.except_osv(_('Error!'), _('No breakfast defined'))

                    if len(lid) != 0:
                        if lnchid:
                            amount_untaxed = amount_untaxed + (len(lid) * lnch)
                            for c in tax_obj.compute_all(self._cr, self._uid, ltax, lnch, len(lid), lnchid)['taxes']:
                                amount_tax += c.get('amount', 0.0)
                        else:
                            raise osv.except_osv(_('Error!'), _('No lunch defined'))
                    if len(did) != 0:
                        if dnnrid:
                            amount_untaxed = amount_untaxed + (len(did) * dnnr)
                            for c in tax_obj.compute_all(self._cr, self._uid, dtax, dnnr, len(did), dnnrid)['taxes']:
                                amount_tax += c.get('amount', 0.0)
                        else:
                            raise osv.except_osv(_('Error!'), _('No dinner defined'))
                    for line in record.event_tab:
                        eid = self.pool.get('event.event.ticket').search(self._cr, self._uid,
                                                                         [('event_id', '=', line.event_name.id),
                                                                          ('id', '=', line.ticket_type.id)])
                        ticket = self.pool.get('event.event.ticket').browse(self._cr, self._uid, eid,
                                                                            context=self._context)
                        amount_untaxed = amount_untaxed + line.price
                        for c in tax_obj.compute_all(self._cr, self._uid, ticket.product_id.taxes_id, ticket.price, 1,
                                                     ticket.product_id.id)['taxes']:
                            amount_tax += c.get('amount', 0.0)
                    for line in record.service_tab:
                        if line.service_name:
                            amount_untaxed = amount_untaxed + line.total
                            for c in tax_obj.compute_all(self._cr, self._uid, line.service_name.taxes_id, line.price,
                                                         line.quantity, line.service_name.product_id.id)['taxes']:
                                amount_tax += c.get('amount', 0.0)
                    for line in record.amenity_tab:
                        if line.amenities_name:
                            amount_untaxed = amount_untaxed + line.total
                            for c in tax_obj.compute_all(self._cr, self._uid, line.amenities_name.taxes_id, line.price,
                                                         line.quantity, line.amenities_name.product_id.id)['taxes']:
                                amount_tax += c.get('amount', 0.0)

                    self.amount_untaxed = cur_obj.round(self._cr, self._uid, cur, amount_untaxed)
                    self.amount_tax = cur_obj.round(self._cr, self._uid, cur, amount_tax)
                    self.amount_total = self.amount_untaxed + self.amount_tax
                    # res[record.id]['amount_untaxed'] = cur_obj.round(self._cr, self._uid, cur, amount_untaxed)
                    # res[record.id]['amount_total'] = res[record.id]['amount_untaxed'] + res[record.id]['amount_tax']
                return res
            else:
                raise osv.except_osv(_('Error!'), _('No meals defined'))

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        brkid = 0.0
        lnchid = 0.0
        dnnrid = 0.0
        amount_untaxed = 0.0
        amount_tax = 0.0
        amount_total = 0.0
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        mid = self.pool.get('hotel.meal').search(cr, uid, [], context=context)
        hotel_ids = self.browse(cr, uid, ids, context=context)
        if mid or (bool(hotel_ids.meals_tab) == False):

            pricelist = hotel_ids.pricelist_id.id
            partner_id = hotel_ids.partner_id.id
            order_date = hotel_ids.order_date
            qty = 1

            for meals in self.pool.get('hotel.meal').browse(cr, uid, mid, context=context):

                if meals.is_types == 1:
                    brfst = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                         meals.product_id.id, qty or 1.0, partner_id, {
                                                                             'uom': meals.product_id.uom_id.id,
                                                                             'date': order_date,
                                                                         })[pricelist]
                    brkid = meals.product_id.id
                    btax = meals.product_id.taxes_id

                elif meals.is_types == 3:

                    lnch = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                        meals.product_id.id, qty or 1.0, partner_id, {
                                                                            'uom': meals.product_id.uom_id.id,
                                                                            'date': order_date,
                                                                        })[pricelist]
                    lnchid = meals.product_id.id
                    ltax = meals.product_id.taxes_id

                elif meals.is_types == 2:
                    dnnr = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                        meals.product_id.id, qty or 1.0, partner_id, {
                                                                            'uom': meals.product_id.uom_id.id,
                                                                            'date': order_date,
                                                                        })[pricelist]
                    dnnrid = meals.product_id.id
                    dtax = meals.product_id.taxes_id

            for record in self.browse(cr, uid, ids, context=context):
                res[record.id] = {
                    'amount_untaxed': 0.0,
                    'amount_tax': 0.0,
                    'amount_total': 0.0,
                }
                bid = self.pool.get('hotel.meals').search(cr, uid,
                                                          [('breakfast', '=', True), ('book_id', '=', record.id)])
                lid = self.pool.get('hotel.meals').search(cr, uid, [('lunch', '=', True), ('book_id', '=', record.id)])
                did = self.pool.get('hotel.meals').search(cr, uid, [('dinner', '=', True), ('book_id', '=', record.id)])
                cur = record.pricelist_id.currency_id
                for line in record.accom_tab:
                    if line.bed_type:
                        amount_untaxed = amount_untaxed + line.cost
                        for c in tax_obj.compute_all(cr, uid, line.bed_type.taxes_id, line.cost, 1, line.bed_type.id)[
                            'taxes']:
                            amount_tax += c.get('amount', 0.0)

                if len(bid) != 0:
                    if brkid:
                        amount_untaxed = amount_untaxed + (len(bid) * brfst)
                        for c in tax_obj.compute_all(cr, uid, btax, brfst, len(bid), brkid)['taxes']:
                            amount_tax += c.get('amount', 0.0)
                    else:
                        raise osv.except_osv(_('Error!'), _('No breakfast defined'))

                if len(lid) != 0:
                    if lnchid:
                        amount_untaxed = amount_untaxed + (len(lid) * lnch)
                        for c in tax_obj.compute_all(cr, uid, ltax, lnch, len(lid), lnchid)['taxes']:
                            amount_tax += c.get('amount', 0.0)
                    else:
                        raise osv.except_osv(_('Error!'), _('No lunch defined'))
                if len(did) != 0:
                    if dnnrid:
                        amount_untaxed = amount_untaxed + (len(did) * dnnr)
                        for c in tax_obj.compute_all(cr, uid, dtax, dnnr, len(did), dnnrid)['taxes']:
                            amount_tax += c.get('amount', 0.0)
                    else:
                        raise osv.except_osv(_('Error!'), _('No dinner defined'))
                for line in record.event_tab:
                    eid = self.pool.get('event.event.ticket').search(cr, uid, [('event_id', '=', line.event_name.id),
                                                                               ('id', '=', line.ticket_type.id)])
                    ticket = self.pool.get('event.event.ticket').browse(cr, uid, eid, context=context)
                    amount_untaxed = amount_untaxed + line.price
                    for c in \
                    tax_obj.compute_all(cr, uid, ticket.product_id.taxes_id, ticket.price, 1, ticket.product_id.id)[
                        'taxes']:
                        amount_tax += c.get('amount', 0.0)
                for line in record.service_tab:
                    if line.service_name:
                        amount_untaxed = amount_untaxed + line.total
                        for c in tax_obj.compute_all(cr, uid, line.service_name.taxes_id, line.price, line.quantity,
                                                     line.service_name.product_id.id)['taxes']:
                            amount_tax += c.get('amount', 0.0)
                for line in record.amenity_tab:
                    if line.amenities_name:
                        amount_untaxed = amount_untaxed + line.total
                        for c in tax_obj.compute_all(cr, uid, line.amenities_name.taxes_id, line.price, line.quantity,
                                                     line.amenities_name.product_id.id)['taxes']:
                            amount_tax += c.get('amount', 0.0)

                res[record.id]['amount_tax'] = cur_obj.round(cr, uid, cur, amount_tax)
                res[record.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, amount_untaxed)
                res[record.id]['amount_total'] = res[record.id]['amount_untaxed'] + res[record.id]['amount_tax']
            return res
        else:
            raise osv.except_osv(_('Error!'), _('No meals defined'))

    _payment_block_proxy = lambda self, *a, **kw: self._portal_payment_block(*a, **kw)

    _columns = {

        'name': fields.char('Booking Reference', required=True, copy=False, select=True),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True, readonly=True, ondelete='cascade',
                                      states={'draft': [('readonly', False)]}),
        'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, readonly=True,
                                        states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                        help="Pricelist for current reservation. "),
        'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True,
                                              states={'draft': [('readonly', False)],
                                                      'pre_reserved': [('readonly', False)]},
                                              help="Invoice address for current reservation. "),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=True,
                                               states={'draft': [('readonly', False)],
                                                       'pre_reserved': [('readonly', False)]},
                                               help="Delivery address for current reservation. "),
        'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency",
                                      string="Currency", readonly=True),
        'order_date': fields.datetime(string='Booking Date', required=True, readonly=True,
                                      states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                      copy=False),
        'rsrv_from': fields.date(string='Reservation From', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'rsrv_to': fields.date(string='Reservation To', required=True, readonly=True,
                               states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'accom_tab': fields.one2many('hotel.accommodation', 'book_id', 'Accommodation', readonly=True,
                                     states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                     copy=False),
        'meals_tab': fields.one2many('hotel.meals', 'book_id', 'Meals', readonly=True,
                                     states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                     copy=False),
        'event_tab': fields.one2many('hotel.events', 'book_id', 'Events', readonly=True,
                                     states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                     copy=True),
        'service_tab': fields.one2many('hotel.bookservice', 'book_id', 'Service', readonly=True,
                                       states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                       copy=False),
        'amenity_tab': fields.one2many('hotel.amenitiesbook', 'book_id', 'Amenities', readonly=True,
                                       states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]},
                                       copy=False),
        'state': fields.selection(
            [('draft', 'Draft'), ('pre_reserved', 'Pre-Reserved'), ('confirm', 'Confirm'), ('cancel', 'Cancel'),
             ('done', 'Done')], 'State', readonly=True, copy=False),
        'accom_sum': fields.one2many('hotel.accommodationsummery', 'reservation_id', 'Accommodation', readonly=True),
        'meals_sum': fields.one2many('hotel.mealssummery', 'reservation_id', 'Meals', readonly=True, copy=False),
        'accom_typ': fields.many2one('product.category', 'Default Accommodation Type', readonly=True,
                                     states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'events_sum': fields.one2many('hotel.eventsummery', 'reservation_id', 'Events', readonly=True),
        'service_sum': fields.one2many('hotel.servicesummery', 'reservation_id', 'Services', readonly=True),
        'amenity_sum': fields.one2many('hotel.amenitiesummery', 'reservation_id', 'Services', readonly=True),
        'evenr_reg': fields.one2many('event.registration', 'reservation_id', 'Event Registration', readonly=True),
        'sale_order': fields.one2many('sale.order', 'reservation_id', 'Event Registration', readonly=True),
        # 'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
        #     store={
        #         'hotel.book': (lambda self, cr, uid, ids, c={}: ids, ['accom_tab', 'meals_tab', 'event_tab', 'service_tab'], 10),
        #         'hotel.accommodation': (_get_order_accom, ['cost', 'bed_type'], 10),
        #         'hotel.meals': (_get_order_meals, ['breakfast', 'lunch', 'dinner'], 10),
        #         'hotel.events': (_get_order_events, ['price', 'event_name'], 10),
        #         'hotel.bookservice': (_get_order_service, ['price', 'service_name'], 10),
        #         'hotel.amenitiesbook': (_get_order_amenities, ['price', 'amenities_name'], 10), },
        #     multi='sums', help="The amount without tax.", track_visibility='always'),
        # 'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes Amount',
        #     store={
        #         'hotel.book': (lambda self, cr, uid, ids, c={}: ids, ['accom_tab', 'meals_tab', 'event_tab', 'service_tab'], 10),
        #         'hotel.accommodation': (_get_order_accom, ['cost', 'bed_type'], 10),
        #         'hotel.meals': (_get_order_meals, ['breakfast', 'lunch', 'dinner'], 10),
        #         'hotel.events': (_get_order_events, ['price', 'event_name'], 10),
        #         'hotel.bookservice': (_get_order_service, ['price', 'service_name'], 10),
        #         'hotel.amenitiesbook': (_get_order_amenities, ['price', 'amenities_name'], 10), },
        #     multi='sums', help="The tax amount."),
        # 'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Amount',
        #     store={
        #         'hotel.book': (lambda self, cr, uid, ids, c={}: ids, ['accom_tab', 'meals_tab', 'event_tab', 'service_tab'], 10),
        #         'hotel.accommodation': (_get_order_accom, ['cost', 'bed_type'], 10),
        #         'hotel.meals': (_get_order_meals, ['breakfast', 'lunch', 'dinner'], 10),
        #         'hotel.events': (_get_order_events, ['price', 'event_name'], 10),
        #         'hotel.bookservice': (_get_order_service, ['price', 'service_name'], 10),
        #         'hotel.amenitiesbook': (_get_order_amenities, ['price', 'amenities_name'], 10), },
        #     multi='sums', help="The Total amount."),
        'is_accom': fields.boolean('Have an Accommodation', readonly=True,
                                   states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'is_meal': fields.boolean('Want Food', readonly=True,
                                  states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'is_break': fields.boolean('Have Breakfast for All Days', readonly=True,
                                   states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'is_lunch': fields.boolean('Have Lunch for All Days', readonly=True,
                                   states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'is_dinner': fields.boolean('Have Dinner for All Days', readonly=True,
                                    states={'draft': [('readonly', False)], 'pre_reserved': [('readonly', False)]}),
        'is_pay': fields.boolean('Is Payment'),
        'portal_payment_options': fields.function(_payment_block_proxy, type="html", string="Portal Payment Options"),
        'company_id': fields.many2one('res.company', string=_('Company'), change_default=True, required=True,
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'move_ids': fields.many2many('account.move', 'hotel_book_move_rel', 'book_reference_id', 'move_id',
                                     string=_('Advance Payment'),
                                     readonly=True, index=True, ondelete='restrict', copy=False,
                                     ),
        'balance_amount': fields.float('Balance Amount', compute='_compute_total_amount', readonly=True),
        'amount_untaxed': fields.float('Untaxed Amount', compute='_compute_total_amount1', readonly=True),
        'amount_tax': fields.float('Taxes Amount', compute='_compute_total_amount1', readonly=True),
        'amount_total': fields.float('The Total Amount', compute='_compute_total_amount1', readonly=True),
        'advance_amount': fields.float('Advance Amount', readonly=True),
    }

    _defaults = {

        'name': '/',
        'order_date': fields.datetime.now,
        'state': 'draft',
        'is_pay': False,
        'amount_untaxed': 0.0,
        'amount_tax': 0.0,
        'amount_total': 0.0,
        'balance_amount': 0.0,
        'advance_amount': 0.0,
        'company_id': _default_company,
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        if not partner_id:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, }}
        partner_obj = self.pool.get('res.partner')
        addr = partner_obj.address_get(cr, uid, [partner_id], ['delivery', 'invoice', 'contact'])
        pricelist = partner_obj.browse(cr, uid, partner_id).property_product_pricelist.id
        ##################################################################################################
        partner_rec = self.pool.get('res.partner').browse(cr, uid, partner_id, context)
        name = partner_rec.name
        email = partner_rec.email
        phone = partner_rec.phone
        reg_obje = self.pool.get('event.registration')
        if ids:
            reg_ids = reg_obje.search(cr, uid, [('reservation_id', '=', ids[0])])
            for reg_id in reg_ids:
                for reg in reg_obje.browse(cr, uid, reg_id, context=context):
                    reg_obje.write(cr, uid, reg.id, {'name': name, 'email': email, 'phone': phone}, context=context)
        return {'value': {'partner_invoice_id': addr['invoice'], 'partner_shipping_id': addr['delivery'],
                          'pricelist_id': pricelist}}

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, accom_tab, meals_tab, event_tab, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id,
                                                                     context=context).currency_id.id
        }
        if not accom_tab or meals_tab or event_tab:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message': _(
                'If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}

    def action_confirm_function(self, cr, uid, ids, context=None):

        reg_obje = self.pool.get('event.registration')
        reg_id = reg_obje.search(cr, uid, [('reservation_id', '=', ids[0])])
        for reg in reg_obje.browse(cr, uid, reg_id, context=context):
            reg_obje.write(cr, uid, reg.id, {'state': 'open'}, context=context)
        res = self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return res

    def action_create_reserv(self, cr, uid, ids, context=None):
        reg_obj = self.pool.get('event.registration')
        reg_id = reg_obj.search(cr, uid, [('reservation_id', '=', ids[0])])
        res = self.write(cr, uid, ids, {'state': 'pre_reserved'}, context=context)
        for reg in reg_obj.browse(cr, uid, reg_id, context=context):
            reg_obj.write(cr, uid, reg.id, {'state': 'pre_reserved'}, context=context)
        return res

    def action_create_prereserv(self, cr, uid, ids, context=None):
        res = self.write(cr, uid, ids, {'state': 'pre_reserved'}, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        bed_lis = []
        mid = self.pool.get('hotel.meal').search(cr, uid, [], context=context)

        pricelist = vals['pricelist_id']
        partner_id = vals['partner_id']
        order_date = vals.get('order_date')
        qty = 1
        if order_date:
            if type(order_date) != str and type(order_date) != unicode:
                order_date = order_date.strftime('%Y-%m-%d')

        for meals in self.pool.get('hotel.meal').browse(cr, uid, mid, context=context):
            if meals.is_types == 1:
                brfst = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                     meals.product_id.id, qty or 1.0, partner_id, {
                                                                         'uom': meals.product_id.uom_id.id,
                                                                         'date': order_date,
                                                                     })[pricelist]
                brkid = meals.product_id.id
            elif meals.is_types == 3:
                lnch = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                    meals.product_id.id, qty or 1.0, partner_id, {
                                                                        'uom': meals.product_id.uom_id.id,
                                                                        'date': order_date,
                                                                    })[pricelist]
                lnchid = meals.product_id.id
            elif meals.is_types == 2:
                dnnr = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                    meals.product_id.id, qty or 1.0, partner_id, {
                                                                        'uom': meals.product_id.uom_id.id,
                                                                        'date': order_date,
                                                                    })[pricelist]
                dnnrid = meals.product_id.id
        if context is None:
            context = {}
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'hotel.book') or '/'
            new_id = super(hotel_book, self).create(cr, uid, vals, context=context)
        if new_id:
            accom_obj = self.pool.get('hotel.accommodationsummery')
            meals_obj = self.pool.get('hotel.mealssummery')
            event_obj = self.pool.get('hotel.eventsummery')
            service_obj = self.pool.get('hotel.servicesummery')
            amenities_obj = self.pool.get('hotel.amenitiesummery')
            event_reg_obj = self.pool.get('event.registration')

            ########################### Code for Creating Summery ###########################################
            bid = self.pool.get('hotel.meals').search(cr, uid, [('breakfast', '=', True), ('book_id', '=', new_id)])
            lid = self.pool.get('hotel.meals').search(cr, uid, [('lunch', '=', True), ('book_id', '=', new_id)])
            did = self.pool.get('hotel.meals').search(cr, uid, [('dinner', '=', True), ('book_id', '=', new_id)])
            for record in self.browse(cr, uid, new_id, context=context):
                accom_vals = {}
                meals_vals = {}
                event_vals = {}
                service_vals = {}
                reg_vals = {}
                for line in record.accom_tab:
                    if line.bed_type:
                        if line.bed_type.id not in bed_lis:
                            pid = self.pool.get('hotel.accommodation').search(cr, uid,
                                                                              [('bed_type', '=', line.bed_type.id),
                                                                               ('book_id', '=', new_id)])
                            accom_vals = {
                                'product_id': line.bed_type.id,
                                'price_unit': line.cost,
                                'name': line.accom_type.name,
                                'product_uom_qty': len(pid),
                                'pricelist_id': record.pricelist_id.id,
                                'tax_id': line.bed_type.taxes_id,
                                'reservation_id': record.id,
                            }
                            accom_obj.create(cr, uid, accom_vals, context=context)
                            bed_lis.append(line.bed_type.id)
                if len(bid) != 0:
                    meals_vals = {
                        'product_id': brkid,
                        'price_unit': brfst,
                        'name': 'Breakfast',
                        'product_uom_qty': len(bid),
                        'pricelist_id': record.pricelist_id.id,
                        'reservation_id': record.id,
                    }
                    meals_obj.create(cr, uid, meals_vals, context=context)
                if len(lid) != 0:
                    meals_vals = {
                        'product_id': lnchid,
                        'price_unit': lnch,
                        'name': 'Lunch',
                        'product_uom_qty': len(lid),
                        'pricelist_id': record.pricelist_id.id,
                        'reservation_id': record.id,
                    }
                    meals_obj.create(cr, uid, meals_vals, context=context)
                if len(did) != 0:
                    meals_vals = {
                        'product_id': dnnrid,
                        'price_unit': dnnr,
                        'name': 'Dinner',
                        'product_uom_qty': len(did),
                        'pricelist_id': record.pricelist_id.id,
                        'reservation_id': record.id,
                    }
                    meals_obj.create(cr, uid, meals_vals, context=context)
                for line in record.event_tab:
                    eid = self.pool.get('event.event.ticket').search(cr, uid, [('event_id', '=', line.event_name.id),
                                                                               ('id', '=', line.ticket_type.id)])
                    ticket = self.pool.get('event.event.ticket').browse(cr, uid, eid, context=context)
                    reg_vals = {
                        'event_id': line.event_name.id,
                        'partner_id': record.partner_id.id,
                        'name': record.partner_id.name,
                        'email': record.partner_id.email,
                        'phone': record.partner_id.phone,
                        'nb_register': 1,
                        'event_ticket_id': ticket.id,
                        'reservation_id': record.id,
                        'state': 'draft',
                    }

                    event_reg_obj.create(cr, uid, reg_vals, context=context)
                    event_vals = {
                        'product_id': ticket.product_id.id,
                        'price_unit': line.price,
                        'name': ticket.name,
                        'pricelist_id': record.pricelist_id.id,
                        'product_uom_qty': 1,
                        'reservation_id': record.id,
                        'hotel_event_id': line.id
                    }
                    event_obj.create(cr, uid, event_vals, context=context)
                for line in record.service_tab:
                    if line.service_name:
                        service_vals = {
                            'product_id': line.service_name.product_id.id,
                            'price_unit': line.price,
                            'name': line.description,
                            'product_uom_qty': line.quantity,
                            'pricelist_id': record.pricelist_id.id,
                            'tax_id': line.service_name.taxes_id,
                            'reservation_id': record.id,
                            'hotel_service_id': line.id
                        }
                    service_obj.create(cr, uid, service_vals, context=context)
                for line in record.amenity_tab:
                    if line.amenities_name:
                        amenity_vals = {
                            'product_id': line.amenities_name.product_id.id,
                            'price_unit': line.price,
                            'name': line.description,
                            'product_uom_qty': line.quantity,
                            'pricelist_id': record.pricelist_id.id,
                            'tax_id': line.amenities_name.taxes_id,
                            'reservation_id': record.id,
                            'hotel_amenity_id': line.id
                        }
                        amenities_obj.create(cr, uid, amenity_vals, context=context)

                    ##################################### Code for Creating Summery ######################################
            return new_id

    def write(self, cr, uid, ids, values, context=None):
        partner = self.browse(cr, uid, ids, context).partner_id.id
        bed_lis = []
        event_list = []
        service_list = []
        reg_list = []
        aminities_list = []
        brfst = 0.0
        brkid = 0
        lnch = 0.0
        lnchid = 0
        dnnr = 0.0
        dnnrid = 0
        pricelist = False
        partner_id = False
        order_date = False
        hotel_ids = self.browse(cr, uid, ids, context=context)
        pricelist = hotel_ids.pricelist_id.id
        partner_id = hotel_ids.partner_id.id
        order_date = hotel_ids.order_date

        qty = 1
        res = super(hotel_book, self).write(cr, uid, ids, values, context=context)

        if pricelist and partner_id and order_date:
            mid = self.pool.get('hotel.meal').search(cr, uid, [], context=context)
            for meals in self.pool.get('hotel.meal').browse(cr, uid, mid, context=context):
                if meals.is_types == 1:
                    brfst = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                         meals.product_id.id, qty or 1.0, partner_id, {
                                                                             'uom': meals.product_id.uom_id.id,
                                                                             'date': order_date,
                                                                         })[pricelist]
                    brkid = meals.product_id.id
                elif meals.is_types == 3:
                    lnch = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                        meals.product_id.id, qty or 1.0, partner_id, {
                                                                            'uom': meals.product_id.uom_id.id,
                                                                            'date': order_date,
                                                                        })[pricelist]
                    lnchid = meals.product_id.id
                elif meals.is_types == 2:
                    dnnr = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                        meals.product_id.id, qty or 1.0, partner_id, {
                                                                            'uom': meals.product_id.uom_id.id,
                                                                            'date': order_date,
                                                                        })[pricelist]
                    dnnrid = meals.product_id.id

                ##########################Code for updating Summery #####################################

        accom_obj = self.pool.get('hotel.accommodationsummery')
        meals_obj = self.pool.get('hotel.mealssummery')
        event_obj = self.pool.get('hotel.eventsummery')
        service_obj = self.pool.get('hotel.servicesummery')
        amenities_obj = self.pool.get('hotel.amenitiesummery')
        event_reg_obj = self.pool.get('event.registration')
        for record in self.browse(cr, uid, ids, context=context):
            accom_vals = {}
            meals_vals = {}
            event_vals = {}
            reg_vals = {}
            for line in record.accom_tab:
                if line.bed_type:
                    if line.bed_type.id not in bed_lis:
                        pid = self.pool.get('hotel.accommodation').search(cr, uid, [('bed_type', '=', line.bed_type.id),
                                                                                    ('book_id', '=', record.id)])
                        accom_vals = {
                            'product_id': line.bed_type.id,
                            'price_unit': line.cost,
                            'name': line.accom_type.name,
                            'product_uom_qty': len(pid),
                            'pricelist_id': record.pricelist_id.id,
                            'tax_id': line.bed_type.taxes_id,
                            'reservation_id': record.id,
                        }
                        acomsum_id = accom_obj.search(cr, uid, [('product_id', '=', line.bed_type.id),
                                                                ('reservation_id', '=', record.id)])
                        if not acomsum_id:
                            accom_obj.create(cr, uid, accom_vals, context=context)
                        else:
                            accom = accom_obj.browse(cr, uid, acomsum_id, context=context)
                            accom_obj.write(cr, uid, accom.id, accom_vals, context=context)
                        bed_lis.append(line.bed_type.id)
            acomcheck_id = accom_obj.search(cr, uid, [('reservation_id', '=', record.id)])
            for check_prod in accom_obj.browse(cr, uid, acomcheck_id, context=context):
                if check_prod.product_id.id not in bed_lis:
                    accom_obj.unlink(cr, uid, [check_prod.id], context=context)

            bid = self.pool.get('hotel.meals').search(cr, uid, [('breakfast', '=', True), ('book_id', '=', record.id)])
            lid = self.pool.get('hotel.meals').search(cr, uid, [('lunch', '=', True), ('book_id', '=', record.id)])
            did = self.pool.get('hotel.meals').search(cr, uid, [('dinner', '=', True), ('book_id', '=', record.id)])
            mealsum_id = meals_obj.search(cr, uid, [('product_id', '=', brkid), ('reservation_id', '=', record.id)])
            meal = meals_obj.browse(cr, uid, mealsum_id, context=context)
            if len(bid) != 0:
                meals_vals = {
                    'product_id': brkid,
                    'price_unit': brfst,
                    'name': 'Breakfast',
                    'product_uom_qty': len(bid),
                    'pricelist_id': record.pricelist_id.id,
                    'reservation_id': record.id,
                }
                if not mealsum_id:
                    meals_obj.create(cr, uid, meals_vals, context=context)
                else:

                    meals_obj.write(cr, uid, meal.id, meals_vals, context=context)
            else:
                if meal.id:
                    meals_obj.unlink(cr, uid, [meal.id], context=context)
            mealsum_id = meals_obj.search(cr, uid, [('product_id', '=', lnchid), ('reservation_id', '=', record.id)])
            meal = meals_obj.browse(cr, uid, mealsum_id, context=context)
            if len(lid) != 0:
                meals_vals = {
                    'product_id': lnchid,
                    'price_unit': lnch,
                    'name': 'Lunch',
                    'product_uom_qty': len(lid),
                    'pricelist_id': record.pricelist_id.id,
                    'reservation_id': record.id,
                }
                if not mealsum_id:
                    meals_obj.create(cr, uid, meals_vals, context=context)
                else:
                    meals_obj.write(cr, uid, meal.id, meals_vals, context=context)
            else:
                if meal.id:
                    meals_obj.unlink(cr, uid, [meal.id], context=context)
            mealsum_id = meals_obj.search(cr, uid, [('product_id', '=', dnnrid), ('reservation_id', '=', record.id)])
            meal = meals_obj.browse(cr, uid, mealsum_id, context=context)
            if len(did) != 0:
                meals_vals = {
                    'product_id': dnnrid,
                    'price_unit': dnnr,
                    'name': 'Dinner',
                    'product_uom_qty': len(did),
                    'pricelist_id': record.pricelist_id.id,
                    'reservation_id': record.id,
                }
                if not mealsum_id:
                    meals_obj.create(cr, uid, meals_vals, context=context)
                else:
                    meals_obj.write(cr, uid, meal.id, meals_vals, context=context)
            else:
                if meal.id:
                    meals_obj.unlink(cr, uid, [meal.id], context=context)

            for line in record.event_tab:
                eid = self.pool.get('event.event.ticket').search(cr, uid, [('event_id', '=', line.event_name.id),
                                                                           ('id', '=', line.ticket_type.id)])
                ticket = self.pool.get('event.event.ticket').browse(cr, uid, eid, context=context)
                reg_vals = {
                    'event_id': line.event_name.id,
                    'partner_id': record.partner_id.id,
                    'name': record.partner_id.name,
                    'email': record.partner_id.email,
                    'phone': record.partner_id.phone,
                    'nb_register': 1,
                    'event_ticket_id': ticket.id,
                    'reservation_id': record.id,
                    'state': 'draft',
                }
                event_vals = {
                    'product_id': ticket.product_id.id,
                    'price_unit': line.price,
                    'name': ticket.name,
                    'product_uom_qty': 1,
                    'pricelist_id': record.pricelist_id.id,
                    'reservation_id': record.id,
                    'hotel_event_id': line.id
                }
                evntsum_id = event_obj.search(cr, uid, [('hotel_event_id', '=', line.id)])
                if not evntsum_id:
                    event_obj.create(cr, uid, event_vals, context=context)
                    event_reg_obj.create(cr, uid, reg_vals, context=context)
                else:
                    event = event_obj.browse(cr, uid, evntsum_id, context=context)
                    event_obj.write(cr, uid, event.id, event_vals, context=context)
                event_list.append(line.id)
                reg_list.append(ticket.id)

            regcheck_id = event_reg_obj.search(cr, uid, [('reservation_id', '=', record.id)])
            for reg in event_reg_obj.browse(cr, uid, regcheck_id, context=context):
                if reg.event_ticket_id.id not in reg_list:
                    self.pool.get('event.event.ticket').write(cr, uid, reg.event_ticket_id.id,
                                                              {'seat_available': reg.event_ticket_id.seat_available + 1,
                                                               'seats_available': reg.event_ticket_id.seats_available + 1})
                    event_reg_obj.unlink(cr, uid, [reg.id], context=context)

            eventcheck_id = event_obj.search(cr, uid, [('reservation_id', '=', record.id)])
            for event_prod in event_obj.browse(cr, uid, eventcheck_id, context=context):
                if event_prod.hotel_event_id not in event_list:
                    event_obj.unlink(cr, uid, [event_prod.id], context=context)

            for line in record.service_tab:
                if line.service_name:
                    service_vals = {
                        'product_id': line.service_name.product_id.id,
                        'price_unit': line.price,
                        'name': line.description,
                        'product_uom_qty': line.quantity,
                        'tax_id': line.service_name.taxes_id,
                        'pricelist_id': record.pricelist_id.id,
                        'reservation_id': record.id,
                        'hotel_service_id': line.id
                    }
                    service_id = service_obj.search(cr, uid, [('hotel_service_id', '=', line.id)])

                    if not service_id:
                        service_obj.create(cr, uid, service_vals, context=context)
                    else:
                        service = service_obj.browse(cr, uid, service_id, context=context)
                        service_obj.write(cr, uid, service.id, service_vals, context=context)
                    service_list.append(line.id)
            servicecheck_id = service_obj.search(cr, uid, [('reservation_id', '=', record.id)])
            for service_prod in service_obj.browse(cr, uid, servicecheck_id, context=context):
                if service_prod.hotel_service_id not in service_list:
                    service_obj.unlink(cr, uid, [service_prod.id], context=context)

            for line in record.amenity_tab:
                if line.amenities_name:
                    amenities_vals = {
                        'product_id': line.amenities_name.product_id.id,
                        'price_unit': line.price,
                        'name': line.description,
                        'product_uom_qty': line.quantity,
                        'pricelist_id': record.pricelist_id.id,
                        'tax_id': line.amenities_name.taxes_id,
                        'reservation_id': record.id,
                        'hotel_amenity_id': line.id
                    }
                    amenities_id = amenities_obj.search(cr, uid, [('hotel_amenity_id', '=', line.id)])
                    if not amenities_id:
                        amenities_obj.create(cr, uid, amenities_vals, context=context)
                    else:
                        amenities = amenities_obj.browse(cr, uid, amenities_id, context=context)
                        amenities_obj.write(cr, uid, amenities.id, amenities_vals, context=context)
                    aminities_list.append(line.id)
            amenitycheck_id = amenities_obj.search(cr, uid, [('reservation_id', '=', record.id)])
            for amenity_prod in amenities_obj.browse(cr, uid, amenitycheck_id, context=context):
                if amenity_prod.hotel_amenity_id not in aminities_list:
                    amenities_obj.unlink(cr, uid, [amenity_prod.id], context=context)

                ##########################Code for updating Summery #####################################
        return res

    @api.onchange('rsrv_from')
    def _onchange_from(self):
        if not self.rsrv_to:
            self.rsrv_to = self.rsrv_from
            # self.is_accom = False

    @api.onchange('rsrv_from', 'rsrv_to', 'is_meal')
    def check_date(self):

        res = []
        res1 = []
        list_id = []
        list_id1 = []
        for meal in self.meals_tab:
            res1.append((0, 0, {'meals_date': meal.meals_date,
                                'breakfast': meal.breakfast,
                                'lunch': meal.lunch,
                                'dinner': meal.dinner}))
            list_id.append(meal.meals_date)

        if self.rsrv_from and self.rsrv_to:

            if self.rsrv_from < self.rsrv_to:
                date1 = datetime.strptime(self.rsrv_from, '%Y-%m-%d')
                date2 = datetime.strptime(self.rsrv_to, '%Y-%m-%d')
                delta = date2 - date1
                for i in range(delta.days + 1):
                    date = date1 + td(days=i)
                    date = date.strftime('%Y-%m-%d')
                    if self.is_meal:
                        list_id1.append(date)
            elif self.rsrv_from == self.rsrv_to:
                date1 = datetime.strptime(self.rsrv_from, '%Y-%m-%d')
                date = date1.strftime('%Y-%m-%d')
                if self.is_meal:
                    list_id1.append(date)

            elif self.rsrv_from > self.rsrv_to:
                raise osv.except_osv(_('warning'), _(' From date not longer than To date'))
        if len(list_id) > len(list_id1):
            for meals in self.meals_tab:
                if meals.meals_date in list_id1:
                    res.append((0, 0, {'meals_date': meals.meals_date,
                                       'breakfast': meals.breakfast,
                                       'lunch': meals.lunch,
                                       'dinner': meals.dinner}))
            self.update({'meals_tab': res})

        else:
            for rd1 in list_id1:
                if rd1 not in list_id:
                    res1.append((0, 0, {'meals_date': rd1,
                                        'breakfast': False,
                                        'lunch': False,
                                        'dinner': False}))
            self.update({'meals_tab': res1})

        return {}

    @api.onchange('rsrv_from', 'rsrv_to', 'is_accom', )
    def check_changeaccom(self):
        res = []
        res1 = []
        list_id = []
        list_id1 = []
        for accom in self.accom_tab:
            # res1.append((0, 0, {'accom_date': accom.accom_date,
            #                     'accom_type': accom.accom_type.id,
            #                     'bed_type': accom.bed_type.id,
            #                     'status': accom.status,
            #                     'cost': accom.cost}))
            list_id.append(accom.accom_date)
        if self.rsrv_from and self.rsrv_to:
            if self.rsrv_from < self.rsrv_to:
                date1 = datetime.strptime(self.rsrv_from, '%Y-%m-%d')
                date2 = datetime.strptime(self.rsrv_to, '%Y-%m-%d')
                delta = date2 - date1
                if delta.days >= 1:
                    date_range = delta.days
                else:
                    date_range = delta.days + 1
                for i in range(date_range):
                    date = date1 + td(days=i)
                    date = date.strftime('%Y-%m-%d')
                    if self.is_accom:
                        list_id1.append(date)

            elif self.rsrv_from == self.rsrv_to:
                date1 = datetime.strptime(self.rsrv_from, '%Y-%m-%d')
                date = date1.strftime('%Y-%m-%d')
                if self.is_accom:
                    list_id1.append(date)
        if len(list_id) > len(list_id1):
            for accom in self.accom_tab:
                if accom.accom_date in list_id1:
                    res.append((0, 0, {'accom_date': accom.accom_date,
                                       'accom_type': accom.accom_type.id,
                                       'bed_type': accom.bed_type.id,
                                       'status': accom.status,
                                       'cost': accom.cost}))
            self.accom_tab = False
            self.update({'accom_tab': res})

        else:
            for rd1 in list_id1:
                if rd1 in list_id:
                    for accom in self.accom_tab:
                        if rd1 == accom.accom_date:
                            res1.append((0, 0, {'accom_date': accom.accom_date,
                                                'accom_type': accom.accom_type.id,
                                                'bed_type': accom.bed_type.id,
                                                'status': accom.status,
                                                'cost': accom.cost}))
                else:
                    res1.append((0, 0, {'accom_date': rd1,
                                        'accom_type': self.accom_typ.id,
                                        'bed_type': False,
                                        'status': False,
                                        'cost': False}))
            self.accom_tab = False
            self.update({'accom_tab': res1})
        return {}

    @api.onchange('is_break', 'is_lunch', 'is_dinner')
    def check_change(self):
        res1 = []
        res2 = []
        res3 = []
        if self.is_break:
            for meal in self.meals_tab:
                res1.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': True,
                                    'lunch': meal.lunch,
                                    'dinner': meal.dinner}))
            self.update({'meals_tab': res1})

        if not self.is_break:
            for meal in self.meals_tab:
                res1.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': False,
                                    'lunch': meal.lunch,
                                    'dinner': meal.dinner}))
            self.update({'meals_tab': res1})

        if self.is_lunch:
            for meal in self.meals_tab:
                res2.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': meal.breakfast,
                                    'lunch': True,
                                    'dinner': meal.dinner}))
            self.update({'meals_tab': res2})

        if not self.is_lunch:
            for meal in self.meals_tab:
                res2.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': meal.breakfast,
                                    'lunch': False,
                                    'dinner': meal.dinner}))
            self.update({'meals_tab': res2})

        if self.is_dinner:
            for meal in self.meals_tab:
                res3.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': meal.breakfast,
                                    'lunch': meal.lunch,
                                    'dinner': True}))
            self.update({'meals_tab': res3})

        if not self.is_dinner:
            for meal in self.meals_tab:
                res3.append((0, 0, {'meals_date': meal.meals_date,
                                    'breakfast': meal.breakfast,
                                    'lunch': meal.lunch,
                                    'dinner': False}))
            self.update({'meals_tab': res3})

        return {}

    @api.onchange('accom_typ')
    def check_accom(self):

        res = []

        if self.accom_typ:
            for accom in self.accom_tab:
                bed_list = []
                room_list = []
                vacant_list = []
                room_ids = self.env['product.product'].search([('categ_id', '=', self.accom_typ.id)])
                for record in room_ids:
                    room_list.append(record.id)
                    room_id = self.env['hotel.accommodation'].search([('bed_type', '=', record.id)])
                    for val in room_id:
                        if val.status == 'occupied' and val.accom_date == accom.accom_date:
                            bed_list.append(record.id)
                for item in room_list:
                    if item not in bed_list:
                        vacant_list.append(item)
                room = False
                price = False
                if vacant_list:
                    for i in vacant_list:
                        room = i
                        price = self.accom_tab.product_id_change(self.pricelist_id.id, room, self.partner_id.id,
                                                                 accom.accom_date, self.accom_typ.id)
                        price = price['value']['cost']
                        break
                accom_type = False
                if room:
                    accom_type = self.accom_typ.id
                res.append((0, 0, {'accom_date': accom.accom_date,
                                   'accom_type': accom_type,
                                   'bed_type': room,
                                   'status': 'reserved',
                                   'cost': price, }))
            self.update({'accom_tab': res})
            return {}

    def button_payment(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher',
                                                                             'view_vendor_receipt_dialog_form')
        advance_obj = self.pool.get('hotel.advance')
        advance = advance_obj.browse(cr, uid, advance_obj.search(cr, uid, [('is_active', '=', True)])).advance_pay
        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': _("Pay Advance"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': inv.partner_id.id,
                'default_book_reference_id': inv.id,
                'default_amount': int(advance),
                'default_reference': inv.name,
                'close_after_process': True,
                'default_type': 'receipt',
                'type': 'receipt'
            }
        }

    def view_order(self, cr, uid, ids, context=None):
        folio_pool = self.pool.get('hotel.folio')
        folio_id = folio_pool.search(cr, uid, [('reservation_id', '=', ids[0])])[0]
        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.folio',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': folio_id,
            'target': 'current',

        }
        return res

    @api.multi
    def manual_invoice(self):
        """ create invoices for the given sales orders (ids), and open the form
            view of one of the newly created invoices
        """
        res = self.create_order()
        folio_id = res['res_id']
        folio_rec = self.env['hotel.folio'].browse(folio_id)
        sale_id = folio_rec.order_id
        folio_rec.signal_workflow('order_confirm')
        folio_rec.signal_workflow('manual_invoice')
        invoice_id = sale_id.invoice_ids
        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': invoice_id.id,
            'target': 'current',

        }
        return res

    @api.multi
    def view_invoice(self):
        """
            view of one of the newly created invoices

        """
        folio_pool = self.env['hotel.folio']
        folio_id = folio_pool.search([('reservation_id', '=', self.id),('state', '!=', 'cancel')])[0]
        folio_rec = self.env['hotel.folio'].browse(folio_id.id)
        sale_id = folio_rec.order_id
        invoice_id = sale_id.invoice_ids
        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': invoice_id.id,
            'target': 'current',

        }
        return res

    ########################### Code for Creating Sale Order #################################

    def create_order(self, cr, uid, ids, context=None):
        bed_lis = []
        brfst = 0.0
        brkid = 0
        lnch = 0.0
        lnchid = 0
        dnnr = 0.0
        dnnrid = 0
        order_vals = {}
        cur_obj = self.pool.get('res.currency')
        hotel_obj = self.pool.get('sale.order')
        folio_obj = self.pool.get('hotel.folio')
        bid = self.pool.get('hotel.meals').search(cr, uid, [('breakfast', '=', True), ('book_id', '=', ids[0])])
        lid = self.pool.get('hotel.meals').search(cr, uid, [('lunch', '=', True), ('book_id', '=', ids[0])])
        did = self.pool.get('hotel.meals').search(cr, uid, [('dinner', '=', True), ('book_id', '=', ids[0])])
        mid = self.pool.get('hotel.meal').search(cr, uid, [], context=context)

        hotel_ids = self.browse(cr, uid, ids, context=context)
        pricelist = hotel_ids.pricelist_id.id
        partner_id = hotel_ids.partner_id.id
        order_date = hotel_ids.order_date
        qty = 1

        for meals in self.pool.get('hotel.meal').browse(cr, uid, mid, context=context):
            if meals.is_types == 1:
                brfst = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                     meals.product_id.id, qty or 1.0, partner_id, {
                                                                         'uom': meals.product_id.uom_id.id,
                                                                         'date': order_date,
                                                                     })[pricelist]
                brkid = meals.product_id.id
            elif meals.is_types == 3:
                lnch = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                    meals.product_id.id, qty or 1.0, partner_id, {
                                                                        'uom': meals.product_id.uom_id.id,
                                                                        'date': order_date,
                                                                    })[pricelist]
                lnchid = meals.product_id.id
            elif meals.is_types == 2:
                dnnr = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                    meals.product_id.id, qty or 1.0, partner_id, {
                                                                        'uom': meals.product_id.uom_id.id,
                                                                        'date': order_date,
                                                                    })[pricelist]
                dnnrid = meals.product_id.id
        for record in self.browse(cr, uid, ids, context=context):
            order_lines = []
            accom_vals = {}
            meals_vals = {}
            event_vals = {}
            ad_amount = record.advance_amount
            note_str = _('Prepaid amount: %.2f') % (float(ad_amount))
            order_vals = {
                'date_order': record.order_date,
                'partner_id': record.partner_id.id,
                'pricelist_id': record.pricelist_id.id,
                'partner_invoice_id': record.partner_invoice_id.id,
                'partner_shipping_id': record.partner_shipping_id.id,
                'reservation_id': record.id,
                'reference_id': record.name,
                'note': note_str,
                'state': 'draft',
            }
            for line in record.accom_tab:
                if line.bed_type:
                    if line.bed_type.id not in bed_lis:
                        pid = self.pool.get('hotel.accommodation').search(cr, uid, [('bed_type', '=', line.bed_type.id),
                                                                                    ('book_id', '=', record.id)])
                        order_lines.append((0, 0, {
                            'product_id': line.bed_type.id,
                            'name': "Accommodation: %s" % line.accom_type.name,
                            'product_uom_qty': len(pid),
                            'price_unit': line.cost
                        }))
                        bed_lis.append(line.bed_type.id)
            if len(bid) != 0:
                order_lines.append((0, 0, {
                    'product_id': brkid,
                    'name': 'Meals: Breakfast',
                    'price_unit': brfst,
                    'product_uom_qty': len(bid),
                }))
            if len(lid) != 0:
                order_lines.append((0, 0, {
                    'product_id': lnchid,
                    'name': 'Meals: Lunch',
                    'price_unit': lnch,
                    'product_uom_qty': len(lid),
                }))
            if len(did) != 0:
                order_lines.append((0, 0, {
                    'product_id': dnnrid,
                    'name': 'Meals: Dinner',
                    'price_unit': dnnr,
                    'product_uom_qty': len(did),
                }))
            for line in record.event_tab:
                eid = self.pool.get('event.event.ticket').search(cr, uid, [('event_id', '=', line.event_name.id),
                                                                           ('id', '=', line.ticket_type.id)])
                ticket = self.pool.get('event.event.ticket').browse(cr, uid, eid, context=context)
                order_lines.append((0, 0, {
                    'product_id': ticket.product_id.id,
                    'name': "Events: %s Tickets" % ticket.name,
                    'price_unit': line.price,
                }))
            for line in record.service_tab:
                if line.service_name:
                    order_lines.append((0, 0, {
                        'product_id': line.service_name.product_id.id,
                        'name': 'Services',
                        'price_unit': line.price,
                        'product_uom_qty': line.quantity
                    }))
            for line in record.amenity_tab:
                if line.amenities_name:
                    order_lines.append((0, 0, {
                        'product_id': line.amenities_name.product_id.id,
                        'name': 'Amenities',
                        'price_unit': line.price,
                        'product_uom_qty': line.quantity
                    }))
            order_vals.update({'room_lines': order_lines})
            folio_id = folio_obj.create(cr, uid, order_vals, context=context)
            # cr.execute('insert into hotel_folio_reservation_rel (order_id, invoice_id) values (%s,%s)', (record.id, folio_id))
            self.write(cr, uid, ids, {'state': 'done'}, context=context)

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'hotel_book', 'action_hotel_folio')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        res = mod_obj.get_object_reference(cr, uid, 'hotel_book', 'view_hotel_folio_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = folio_id
        return result

    ########################### Code for Creating Reservation #################################

    def cancel_order(self, cr, uid, ids, context=None):
        folio_pool = self.pool.get('hotel.folio')
        folio_id = folio_pool.search(cr, uid, [('reservation_id', '=', ids[0])])
        if folio_id:
            folio_pool.action_cancel(cr, uid, folio_id, context=context)
        res = False
        accom_obj = self.pool.get('hotel.accommodation')
        evnt_obj = self.pool.get('hotel.events')
        ticket_obj = self.pool.get('event.event.ticket')
        reg_obj = self.pool.get('event.registration')
        event = evnt_obj.search(cr, uid, [('book_id', '=', ids[0])])
        for evnt_id in evnt_obj.browse(cr, uid, event, context=context):
            ticket = ticket_obj.browse(cr, uid, evnt_id.ticket_type.id, context=context)
            ticket_obj.write(cr, uid, ticket.id, {'seat_available': ticket.seat_available + 1,
                                                  'seats_available': ticket.seats_available + 1})
            event_id = reg_obj.search(cr, uid, [('event_ticket_id', '=', ticket.id), ('reservation_id', '=', ids[0])])
            for tcket in reg_obj.browse(cr, uid, event_id, context=context):
                reg_obj.write(cr, uid, tcket.id, {'state': 'cancel'}, context=context)

        book = accom_obj.search(cr, uid, [('book_id', '=', ids[0])])
        for record in accom_obj.browse(cr, uid, book, context=context):
            accom_obj.write(cr, uid, record.id, {'status': 'available'})
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True


#################################### Code for Hotel Booking ###################################



############################ Code for Accommodation ########################################
class hotel_accommodation(osv.osv):
    _name = 'hotel.accommodation'

    @api.one
    def _get_rooom(self):
        print self._context

    _columns = {

        'book_id': fields.many2one('hotel.book', 'Book_id', required=True, select=True, ondelete='cascade'),
        'bed_type': fields.many2one('product.product', 'Rooms',
                                    domain="[('is_room','=',1), ('categ_id', '=', accom_type), ('status', '=', 'available')]"),
        'accom_type': fields.many2one('product.category', 'Accommodation Type', domain="[('is_accom_type','=',1)]"),
        'accom_date': fields.date(string='Date'),
        'status': fields.char('Status'),
        'cost': fields.float('Unit Price'),
    }

    def on_change_accom_date(self, cr, uid, ids, accom_date, rsrv_from, rsrv_to, context=None):

        if accom_date == False:
            print 'Date not Selected'
        elif accom_date < rsrv_from or accom_date > rsrv_to:
            return {
                'value': {
                    'accom_date': False
                },
                'warning': {
                    'title': 'Warning',
                    'message': 'Please select Date between From and To Date'
                }
            }

    def on_change_accom_type(self, cr, uid, ids, accom_type, accom_date, context=None):
        bed_list = []
        room_list = []
        vacant_list = []
        if accom_type and accom_date:
            pid = self.pool.get('product.product').search(cr, uid,
                                                          [('categ_id', '=', accom_type), ('status', '=', 'available')])
            for record in self.pool.get('product.product').browse(cr, uid, pid, context=context):
                room_list.append(record.id)
                roomid = self.search(cr, uid, [('bed_type', '=', record.id)])
                for val in self.browse(cr, uid, roomid, context=context):
                    if val.status == 'occupied' and val.accom_date == accom_date:
                        bed_list.append(record.id)
            for item in room_list:
                if item not in bed_list:
                    vacant_list.append(item)
            domain = {'bed_type': [('id', 'in', vacant_list)]}
            return {'domain': domain, 'value': {'bed_type': False}}
        return {}

    def product_id_change(self, cr, uid, ids, pricelist, bed_type, partner_id, order_date, accom_type, context=None):

        price = 0.0
        qty = 1.0
        product_obj = self.pool.get('product.product')
        if bed_type and accom_type:
            pid = product_obj.search(cr, uid, [('categ_id', '=', accom_type), ('id', '=', bed_type)])
            for record in product_obj.browse(cr, uid, pid, context=context):
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                     bed_type, qty or 1.0, partner_id, {
                                                                         'uom': record.uom_id.id,
                                                                         'date': order_date,
                                                                     })[pricelist]
        return {'value': {'cost': price}}

    _defaults = {

        'status': 'occupied',
    }


############################ Code for Accommodation ########################################



############################## Code for Meals Booking ##################################

class hotel_meals(osv.osv):
    _name = 'hotel.meals'

    def copy(self, cr, uid, id, default=None, context=None):
        return super(hotel_meals, self).copy(cr, uid, id, default=default, context=context)

    @api.one
    @api.depends('book_id.partner_id')
    def checkpartner(self):
        self.partner_id = self.book_id.partner_id

    _columns = {

        'book_id': fields.many2one('hotel.book', 'Book_id', required=True, select=True, ondelete='cascade'),
        'meals_date': fields.date(string='Date', readonly=True),
        'breakfast': fields.boolean('Break Fast'),
        'lunch': fields.boolean('Lunch'),
        'dinner': fields.boolean('Dinner'),
        'partner_id': fields.many2one('res.partner', 'Customer', compute=checkpartner),
        'related_meal': fields.many2one('hotel.mealscount', 'Related Meals')
    }


############################## Code for Meals Booking ##################################


############################### Code for Event Booking #####################################
class hotel_events(osv.osv):
    _name = 'hotel.events'

    def copy(self, cr, uid, id, default=None, context=None):
        return super(hotel_events, self).copy(cr, uid, id, default=default, context=context)

    _columns = {

        'book_id': fields.many2one('hotel.book', 'Book_id', required=True, select=True, ondelete='cascade'),
        'event_name': fields.many2one('event.event', 'Event Name', required=True),
        'ticket_type': fields.many2one('event.event.ticket', 'Ticket Type', required=True),
        'seat_available': fields.integer('Seats Available', readonly=True),
        'price': fields.float('Unit price')

    }

    def on_change_event_name(self, cr, uid, ids, event_name, from_date, to_date, context=None):

        domain = {'ticket_type': [('event_id', '=', event_name), ('deadline', '>=', date.today().strftime('%Y-%m-%d'))],
                  'event_name': [('date_begin', '<=', to_date), ('date_end', '>=', from_date),
                                 ('state', '=', 'confirm')]}
        return {'domain': domain, 'value': {'ticket_type': False, 'seat_available': False, 'price': False}}

    def on_change_ticket_type(self, cr, uid, ids, ticket_type, event_name, partner_id, pricelist, order_date,
                              context=None):

        if ticket_type and event_name:
            ticket_obj = self.pool.get('event.event.ticket').browse(cr, uid, ticket_type, context=context)
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                 ticket_obj.product_id.id, 1.0, partner_id, {
                                                                     'uom': ticket_obj.product_id.uom_id.id,
                                                                     'date': order_date,
                                                                 })[pricelist]
            seats = ticket_obj.seat_available
            if seats == 0:
                raise osv.except_osv(_('warning'), _(' No more ticket available'))
            else:
                return {'value': {'price': price, 'seat_available': seats}}
        return {}

    def create(self, cr, uid, values, context=None):
        ticket_obj = self.pool.get('event.event.ticket')
        evnt_id = ticket_obj.search(cr, uid, [('id', '=', values['ticket_type'])])
        for record in ticket_obj.browse(cr, uid, evnt_id, context=context):
            ticket_obj.write(cr, uid, record.id, {'seat_available': record.seat_available - 1,
                                                  'seats_available': record.seats_available - 1})
        return super(hotel_events, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('ticket_type'):
            ticket_obj = self.pool.get('event.event.ticket')
            evnt_id = ticket_obj.search(cr, uid, [('id', '=', values['ticket_type'])])
            for record in ticket_obj.browse(cr, uid, evnt_id, context=context):
                ticket_obj.write(cr, uid, record.id, {'seat_available': record.seat_available - 1,
                                                      'seats_available': record.seats_available - 1})
        return super(hotel_events, self).write(cr, uid, ids, values, context=context)


############################### Code for Event Booking #####################################


############################## Code for Booking Amenities #################################
class hotel_amenitiesbook(osv.osv):
    _name = 'hotel.amenitiesbook'

    def copy(self, cr, uid, id, default=None, context=None):
        return super(hotel_amenitiesbook, self).copy(cr, uid, id, default=default, context=context)

    @api.one
    @api.depends('price', 'quantity')
    def _get_total(self):
        self.total = self.price * self.quantity

    _columns = {

        'book_id': fields.many2one('hotel.book', 'Book_id', required=True, select=True, ondelete='cascade'),
        'amenities_name': fields.many2one('hotel.amenities', 'Amenities'),
        'quantity': fields.float('Quantity', default=1.0),
        'price': fields.float(string='Unit price'),
        'total': fields.float(compute='_get_total', string='Subtotal', ),
        'description': fields.text('Description'),
    }

    def on_change_amenities(self, cr, uid, ids, amenities_name, pricelist, partner_id, order_date, context=None):
        price = 0.0
        qty = 1.0
        if amenities_name:
            product_id = self.pool.get('hotel.amenities').browse(cr, uid, amenities_name, context=context).product_id.id
            record = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                 product_id, qty or 1.0, partner_id, {
                                                                     'uom': record.uom_id.id,
                                                                     'date': order_date,
                                                                 })[pricelist]
            return {'value': {'price': price, 'total': price}}

    def on_change_qty(self, cr, uid, ids, quantity, price, context=None):
        total = quantity * price
        return {'value': {'total': total}}


############################## Code for Booking Amenities #################################


############################# Code for Service Booking ####################################

class hotel_bookservice(osv.osv):
    _name = 'hotel.bookservice'

    def copy(self, cr, uid, id, default=None, context=None):
        return super(hotel_bookservice, self).copy(cr, uid, id, default=default, context=context)

    @api.one
    @api.depends('price', 'quantity')
    def _get_total(self):
        self.total = self.price * self.quantity

    _columns = {
        'book_id': fields.many2one('hotel.book', 'Book_id', required=True, ondelete='cascade'),
        'service_name': fields.many2one('hotel.services', 'Services'),
        'quantity': fields.float('Quantity', default=1.0),
        'price': fields.float(string='Unit price'),
        'total': fields.float(compute='_get_total', string='Subtotal', ),
        'description': fields.text('Description'),
    }

    def on_change_service(self, cr, uid, ids, service_name, pricelist, partner_id, order_date, context=None):
        price = 0.0
        qty = 1.0
        if service_name:
            product_id = self.pool.get('hotel.services').browse(cr, uid, service_name, context=context).product_id.id
            record = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                 product_id, qty or 1.0, partner_id, {
                                                                     'uom': record.uom_id.id,
                                                                     'date': order_date,
                                                                 })[pricelist]
            return {'value': {'price': price, 'total': price}}

    def on_change_qty(self, cr, uid, ids, quantity, price, context=None):
        total = quantity * price
        return {'value': {'total': total}}


class Event(models.Model):
    _inherit = 'event.registration'

    _columns = {
        'state': fields.selection([
            ('draft', 'Unconfirmed'),
            ('cancel', 'Cancelled'),
            ('pre_reserved', 'Pre-Reserved'),
            ('open', 'Confirmed'),
            ('done', 'Attended'),
        ], string='Status', default='draft', readonly=True, copy=False)
    }
