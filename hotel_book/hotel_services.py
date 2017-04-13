from openerp.osv import osv, fields


## Code for Adding Details of Amenities  ##

class hotel_room(osv.osv):

    _inherit = 'product.product'

    _columns = {

        'is_service': fields.integer('Is Services'),
    }


class hote_room_book(osv.osv):

    _name = 'hotel.services'

    _inherits = {'product.product': 'product_id'}

    _description = 'Services'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product_id', required=True, select=False, ondelete='cascade',
                                      auto_join=True),
        'status': fields.selection([('available', 'Available'), ('not available', 'Not Available')], 'Status'),
    }

    _defaults = {

        'is_service': 1,
        'rental': True,
        'status': 'available',
        'type': 'service',
    }
## Code for Adding Details of Amenities ##

