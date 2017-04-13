from openerp.osv import osv,fields


class hote_document(osv.osv):

    _name = 'hotel.document'

    _rec_name = 'doc_type'

    _columns = {

        'doc_type': fields.char('Document Type', size=50, required=True),
        'doc_code': fields.integer('Document Code', size=50, required=True),
    }


class customer_gender(osv.osv):

    _name = 'customer.gender'

    _rec_name = 'gender_type'

    _columns = {

        'gender_type': fields.char('Gender Type', size=50, required=True)
    }