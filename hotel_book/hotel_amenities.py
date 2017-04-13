from openerp.osv import osv, fields


## Code for Adding Details of Amenities  ##

class hotel_room(osv.osv):

    _inherit = 'product.product'

    _columns = {

        'is_amenity': fields.integer('Is Amenity'),
    }


class hote_room_book(osv.osv):

    _name = 'hotel.amenities'

    _inherits = {'product.product': 'product_id'}

    _description = 'Amenities'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product_id', required=True, select=True, ondelete='cascade', auto_join=True),
        'status': fields.selection([('available', 'Available'), ('not available', 'Not Available')], 'Status'),
    }

    _defaults = {

        'is_amenity': 1,
        'rental': True,
        'status': 'available',
        'type': 'service',
    }
## Code for Adding Details of Amenities ##

