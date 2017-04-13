from openerp.osv import osv, fields
from openerp import api
from openerp.tools.translate import _
import vatnumber

class hotel_customer(osv.osv):

    _inherit = 'res.partner'

    _columns = {

        'dob': fields.date(string='Date of Birth', required=True),
        'gender_id': fields.many2one('customer.gender', 'Gender', required=True),
        'profession': fields.char('Profession', size=100),
        'food_intoler': fields.many2many('hotel.intolerance', 'food_intolerances', 'temp_id', 'food_id', 'Food Intolerances'),
        'diseases': fields.many2many('hotel.diseases', 'medical_diseases', 'temp_id', 'diseases_id', 'Diseases'),
        'allergies': fields.many2many('hotel.allergies', 'medical_allergies', 'temp_id', 'allergies_id', 'Allergies'),
        'doc_type': fields.many2one('hotel.document', 'Document Type', required=True),
        'doc_val': fields.char('Corresponding Document Number', required=True),
        'doc_date': fields.date(string='Document Delivery Date', required=True),
        'doc_exp': fields.date(string='Document Expiry Date', required=True),

    }

    @api.one
    def write(self, vals):
        self.vat_check(vals)
        result = super(hotel_customer, self).write(vals)
        return result

    @api.onchange('doc_date', 'doc_exp')
    def _onchange_check_change(self):
        if self.doc_date and self.doc_exp:
            if self.doc_date > self.doc_exp:
                raise osv.except_osv(_('Warning!'),_(' Document is expired before delivery , please verify'))

    @api.model
    def create(self,vals):
        self.vat_check(vals)
        res = super(hotel_customer,self).create(vals)
        return res

    @api.multi
    def vat_check(self,vals):
        rec = self.browse(self.id)
        if vals.get('doc_type') or vals.get('doc_val'):
            vals['vat'] = False
            vals['vat_subjected'] = False
            if vals.get('doc_type'):
                code = self.env['hotel.document'].browse(vals.get('doc_type')).doc_code
            else:
                code = rec.doc_type.doc_code
            if code == 1:
                if not vals.get('doc_val'):
                    doc_val = rec.doc_val
                else:
                    doc_val = vals['doc_val']
                if vatnumber.check_vat(doc_val):
                    vals['vat'] = doc_val
                    vals['vat_subjected'] = True
                else:
                    raise osv.except_osv(_('Error!'),_(' Not a valid VAT Code, please enter Valid VAT Code'))
            else:
                print 'Method is not called'