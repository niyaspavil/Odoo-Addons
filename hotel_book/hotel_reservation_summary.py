from openerp import fields, models, api, _
from openerp.exceptions import except_orm
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class hotel_room(models.Model):
    _inherit = 'hotel.room'
    _description = 'Hotel Room'

    room_reservation_line_ids = fields.One2many('hotel.room.reservation.line', string='Room Reservation Line',compute='compute_room_lines')

    def compute_room_lines(self):
        self._cr.execute("delete from hotel_room_reservation_line")
        resr_obj = self.pool.get('hotel.room.reservation.line')
        self._cr.execute("select * from hotel_accommodation")
        accom = self._cr.dictfetchall()
        for i in accom:
            book_obj = self.pool.get('hotel.book').browse(self._cr, self._uid, i['book_id'])
            if book_obj.state == 'confirm' or book_obj.state == 'done':
                hotel_search = self.pool.get('hotel.room').search(self._cr, self._uid,[('product_id', '=', i['bed_type'])])
                hotel_obj = self.pool.get('hotel.room').browse(self._cr, self._uid, hotel_search)
                resr_obj.create(self._cr, self._uid, {'date':i['accom_date'], 'room_id': hotel_obj.id,'reservation_id': i['book_id'] })
        resr_search = resr_obj.search(self._cr,self._uid, [('room_id','=',self.id)])
        self.room_reservation_line_ids = resr_search



class hotel_room_reservation_line(models.Model):
    _name = 'hotel.room.reservation.line'
    _description = 'Hotel Room Reservation'
    room_id = fields.Many2one('hotel.room', string='Room id')
    date = fields.Date('Date')
    # check_out = fields.Datetime('Check Out Date', required=True)
    # state = fields.Selection([('assigned', 'Assigned'), ('unassigned', 'Unassigned')], 'Room Status')
    reservation_id = fields.Many2one('hotel.book', string='Reservation')


hotel_room_reservation_line()
class room_reservation_summary(models.Model):
    _name = 'hotel.reservation.summary'
    _description = 'Hotel reservation summary'

    date_from = fields.Datetime('Date From', default=datetime.today())
    date_to = fields.Datetime('Date To')
    summary_header = fields.Text('Summary Header')
    room_summary = fields.Text('Room Summary')
    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(room_reservation_summary, self).default_get(fields)
        if self.date_from == False and self.date_to == False:
            date_today = datetime.today()
            first_day = datetime(date_today.year, date_today.month, 1, 0, 0, 0)
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime(last_temp_day.year, last_temp_day.month, last_temp_day.day, 23, 59, 59)
            date_froms = first_day.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            date_ends = last_day.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            res.update({'date_from': date_froms, 'date_to': date_ends})
        return res

    @api.onchange('date_from', 'date_to')
    def get_room_summary(self):
        '''
         @param self : object pointer
         '''
        res = {}
        all_detail = []
        room_obj = self.env['hotel.room']
        reservation_line_obj = self.env['hotel.room.reservation.line']
        date_range_list = []
        main_header = []
        summary_header_list = ['Rooms']
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise except_orm(_('User Error!'),
                                 _('Please Check Time period Date From can\'t be greater than Date To !'))
            d_frm_obj = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            d_to_obj = datetime.strptime(self.date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            temp_date = d_frm_obj
            while (temp_date <= d_to_obj):
                val = ''
                val = str(temp_date.strftime("%a")) + ' ' + str(temp_date.strftime("%b")) + ' ' + str(
                    temp_date.strftime("%d"))
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
                temp_date = temp_date + timedelta(days=1)
            all_detail.append(summary_header_list)
            room_ids = room_obj.search([])
            all_room_detail = []
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                room_detail.update({'name': room.name or ''})
                self._cr.execute("select * from hotel_accommodation where bed_type = %s", [room.product_id.id])
                accom = self._cr.dictfetchall()
                if not accom:
                    for chk_date in date_range_list:
                        room_list_stats.append({'state': 'Free', 'date': chk_date})
                else:
                    for chk_date in date_range_list:
                        flag = 0
                        for i in accom:
                            book_obj = self.pool.get('hotel.book').browse(self._cr, self._uid, i['book_id'])
                            if i['accom_date'] == chk_date[:10]:
                                flag =  1
                                if book_obj.state == 'confirm' or book_obj.state == 'done':
                                    room_list_stats.append({'state': 'Reserved', 'date': chk_date, 'room_id': room.id})
                                    break;
                                elif book_obj.state == 'draft':
                                    room_list_stats.append({'state': 'Draft', 'date': chk_date, 'room_id': room.id})
                                    break;
                                elif book_obj.state == 'pre_reserved':
                                    room_list_stats.append({'state': 'Pre-reserved', 'date': chk_date, 'room_id': room.id})
                                    break;
                                else:
                                     room_list_stats.append({'state': 'Free', 'date': chk_date, 'room_id': room.id})
                        if flag == 0:
                            room_list_stats.append({'state': 'Free', 'date': chk_date, 'room_id': room.id})
                room_detail.update({'value': room_list_stats})
                all_room_detail.append(room_detail)
            print all_room_detail
            main_header.append({'header': summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res

class quick_room_reservation(models.TransientModel):
    _name = 'quick.room.reservation'
    _description = 'Quick Room Reservation'

    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    check_in = fields.Datetime('Check In', required=True, readonly=True)
    check_out = fields.Datetime('Check Out', required=True)
    room_id = fields.Many2one('hotel.room', 'Room', required=True, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Hotel', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'pricelist', required=True)
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address', required=True)
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact', required=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address', required=True)


    @api.onchange('check_out')
    def on_change_check_out(self):
        '''
          When you change checkout or checkin it will check whether
          Checkout date should be greater than Checkin date
          and update dummy field
          -------------------------------------------------------------
          @param self : object pointer
          @return : raise warning depending on the validation
          '''
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise except_orm(_('Warning'), _('Checkout date should be greater than Checkin date.'))
        if self.check_out:
            check_in = self.check_in
            check_out = self.check_out
            d_frm_obj = datetime.strptime(check_in, DEFAULT_SERVER_DATETIME_FORMAT)
            d_to_obj = datetime.strptime(check_out, DEFAULT_SERVER_DATETIME_FORMAT)
            temp_date = d_frm_obj
            date_range_list = []
            while (temp_date <= d_to_obj):
                date_range_list.append(temp_date.strftime(DEFAULT_SERVER_DATE_FORMAT))
                temp_date = temp_date + timedelta(days=1)
            self._cr.execute("select * from hotel_accommodation where bed_type = %s", [self.room_id.product_id.id])
            accom = self._cr.dictfetchall()
            for entry in accom:
                if entry['accom_date'] in date_range_list:
                    raise except_orm(_('Warning'), _('Room have some booking records for selected period. Pls try with another period..'))




    @api.onchange('partner_id')
    def onchange_partner_id_res(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ----------------------------------------------------------------------
        @param self : object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param fields: List of fields for which we want default values
         @return: A dictionary which of fields with values.
         """
        if self._context is None:
            self._context = {}
        res = super(quick_room_reservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if 'date' in keys:
                res.update({'check_in': self._context['date']})
            if 'room_id' in keys:
                roomid = self._context['room_id']
                res.update({'room_id': int(roomid)})
        return res

    @api.multi
    def room_reserve(self, context=None):
        """
         This method create a new record for hotel.reservation
         -----------------------------------------------------
         @param self: The object pointer
         @return: new record set for hotel reservation.
         """
        hotel_book_obj = self.env['hotel.book']
        for room_resv in self:
            bookng_rcd = hotel_book_obj.create({
                'partner_id': room_resv.partner_id.id,
                'partner_invoice_id': room_resv.partner_invoice_id.id,
                'partner_order_id': room_resv.partner_order_id.id,
                'partner_shipping_id': room_resv.partner_shipping_id.id,
                'rsrv_from': room_resv.check_in,
                'rsrv_to': room_resv.check_out,
                'warehouse_id': room_resv.warehouse_id.id,
                'pricelist_id': room_resv.pricelist_id.id,
                'is_accom': True,
                'accom_typ': room_resv.room_id.categ_id.id,
                'reservation_line': [(0, 0, {
                    'reserve': [(6, 0, [room_resv.room_id.id])],
                    'name': room_resv.room_id and room_resv.room_id.name or ''})]
            })
            bookng_rcd.check_changeaccom()
            qty = 1.0
            price = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [room_resv.pricelist_id.id],
                                room_resv.room_id.product_id.id , qty or 1.0, room_resv.partner_id.id, {
                                'uom': room_resv.room_id.product_id.uom_id.id,
                                })[room_resv.pricelist_id.id]
            accom_obj = self.pool.get('hotel.accommodation')
            accom_search =accom_obj.search(self._cr, self._uid,[('book_id', '=', bookng_rcd.id)])
            accom_obj.write(self._cr, self._uid,accom_search,{'bed_type': room_resv.room_id.product_id.id,'cost': price},context)
            return True
