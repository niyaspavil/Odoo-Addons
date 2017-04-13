from openerp.osv import osv,fields

## Code for Adding Details of Room  ##

class hotel_room(osv.osv):

    _inherit = 'product.product'

    _columns = {

        'is_room': fields.integer('Is Room'),
        'status': fields.selection([('available', 'Available'), ('occupied', 'occupied')], 'Status'),
    }


class hote_room_book(osv.osv):

    _name = 'hotel.room'

    _inherits = {'product.product': 'product_id'}

    _description = 'Room Type'

    _columns = {

        'product_id': fields.many2one('product.product', 'Product_id', required=True, ondelete='cascade',  auto_join=True),
        'floor': fields.many2one('hotel.floor', 'Floor'),
    }

    _defaults = {

        'is_room': 1,
        'rental': True,
        'status': 'available',
        'type': 'service',
    }
## Code for Adding Details of Room ##

