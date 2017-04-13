from openerp.osv import osv,fields

## Code for Accommodation Type ##
class hotel_category(osv.osv):

    _inherit = 'product.category'

    _columns = {

        'is_accom_type': fields.integer('Is Accommodation'),
        'is_amenities': fields.integer('Is Amenities'),
        'is_service': fields.integer('Is Service'),
        'available_in_web': fields.boolean("Show on web")
    }


class hotel_category_accom(osv.osv):

    _name = 'hotel.category'

    _inherits = {'product.category': 'category_id'}

    _description = 'Accommodation Type'

    _columns = {

        'category_id': fields.many2one('product.category', 'category', required=True, select=True, ondelete='cascade'),

    }

    _defaults = {

        'is_accom_type': 1
    }

## Code for Accommodation Type ##


## Code for Amenities Type ##
class hotel_category_amenity(osv.osv):

    _name = 'hotel.amenity'

    _inherits = {'product.category': 'amenity_id'}

    _description = 'Amenities Type'

    _columns = {

        'amenity_id': fields.many2one('product.category', 'Amenity', required=True, select=True, ondelete='cascade'),
    }

    _defaults = {

        'is_amenities': 1
    }
## Code for Amenities Type ##


## Code for Service Type ##
class hotel_category_service(osv.osv):

    _name = 'hotel.service'

    _inherits = {'product.category': 'service_id'}

    _description = 'Service Type'

    _columns = {

        'service_id': fields.many2one('product.category', 'Service', required=True, select=True, ondelete='cascade'),
    }

    _defaults = {

        'is_service': 1
    }
## Code for Service Type ##


## Code for Floor Type ##
class hotel_floor(osv.osv):

    _name = 'hotel.floor'

    _rec_name = 'name'

    _columns = {

        'name': fields.char('Floor Name', size=50, required=True),
        'floor_seq': fields.integer('Sequence'),
    }