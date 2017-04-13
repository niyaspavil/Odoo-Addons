from openerp.osv import osv, fields

class hotel_intolerance(osv.osv):

    _name = 'hotel.intolerance'

    _columns = {

        'name': fields.char('Food Intolerance', required=True),
        'intolerance': fields.text('Description')
    }


class hotel_diseases(osv.osv):

    _name = 'hotel.diseases'

    _columns = {

        'name': fields.char('Diseases', required=True),
        'diseases': fields.text('Description')
    }


class hotel_allergies(osv.osv):

    _name = 'hotel.allergies'

    _columns = {

        'name': fields.char('Allergies', required=True),
        'allergies': fields.text('Description')
    }