from openerp.osv import fields,osv


class hotel_meals(osv.osv):

    _inherit = 'product.product'

    _columns = {

        'is_meals': fields.integer('Is Meals'),
    }


class hote_room_book(osv.osv):

    _name = 'hotel.meal'

    _inherits = {'product.product': 'product_id'}

    _description = 'Meals Type'

    _columns = {
        'book_id': fields.many2one('hotel.book', 'Book_id', select=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product_id', required=True, select=True, ondelete='cascade'),
        'is_types': fields.selection([(1, 'Breakfast'), (2, 'Dinner'), (3, 'Lunch')], 'Food Type', required=True)
    }

    _defaults = {

        'is_meals': 1,
        'type': 'service',
    }

    _sql_constraints = [('is_types_unique', 'unique(is_types)', 'Food Type already exist!')]