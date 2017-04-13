from openerp.osv import osv, fields
from openerp.tools.translate import _



class hotel_advance(osv.osv):

    _name = 'hotel.advance'

    _columns = {

        'advance_pay': fields.float('Advance Payment Amount', required=True),
        'is_active': fields.boolean('Active')
    }

    def create(self, cr, uid, values, context=None):

        active = self.pool.get('hotel.advance').search(cr, uid, [('is_active', '=', True)], context=context)
        if active and values['is_active']:
            raise osv.except_osv(_('warning'), _(' First Inactive Current Payment Amount'))
        else:
            return super(hotel_advance, self).create(cr, uid, values, context=None)
