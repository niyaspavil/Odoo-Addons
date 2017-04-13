from openerp import models, fields, api, osv, netsvc, _
from datetime import date


class hotel_mealscount(models.Model):
    _name = 'hotel.mealscount'

    def compute_total_breakfast(self):
        tkob = self.env['hotel.meals']
        tkrc = tkob.search_count([('meals_date', '=', self._context['date']),('book_id.state', '!=', 'cancel'),('breakfast', '=', True)])
        return tkrc

    def compute_total_lunch(self):
        tkob = self.env['hotel.meals']
        tkrc = tkob.search_count([('meals_date', '=', self._context['date']), ('book_id.state', '!=', 'cancel'),('lunch', '=', True)])
        return tkrc

    def compute_total_dinner(self):
        tkob = self.env['hotel.meals']
        tkrc = tkob.search_count([('meals_date', '=', self._context['date']), ('book_id.state', '!=', 'cancel'), ('dinner', '=', True)])
        return tkrc

    def meals_today_tree(self):

        tkob = self.env['hotel.mealsfilterd']
        tkrc = tkob.search([])
        if tkrc:
            for i in tkrc:
                i.unlink()

        tkob = self.env['hotel.meals']
        tkrc = tkob.search([('meals_date', '=', self._context['date']), ('book_id.state', '!=', 'cancel')])
        entry = []
        for i in tkrc:
            data = {
                'book_id': i.book_id.id,
                'meals_date': i.meals_date,
                'partner_id': i.partner_id.id,
                'breakfast': i.breakfast,
                'lunch': i.lunch,
                'dinner': i.dinner,
            }
            entry.append((0, 0, data))
        return entry

    def date_filter(self):
        return self._context['date']

    breakfastcount = fields.Char(string='Total Breakfast', default=compute_total_breakfast, readonly=True)
    lunchcount = fields.Char(string='Total Lunch', default=compute_total_lunch, readonly=True)
    dinnercount = fields.Char(string='Total Dinner', default=compute_total_dinner, readonly=True)
    related_mealscount = fields.One2many('hotel.meals', 'related_meal', 'Related Meals', default=meals_today_tree)
    filter_date = fields.Date(string='Date', required=True, default=date_filter, readonly=True)


class hotel_meals_filtered(models.Model):
    _name = 'hotel.mealsfilterd'

    book_id = fields.Many2one('hotel.book', 'Book ID', required=True, select=True, ondelete='cascade')
    meals_date = fields.Date(string='Date')
    breakfast = fields.Boolean('Break Fast')
    lunch = fields.Boolean('Lunch')
    dinner = fields.Boolean('Dinner')
    partner_id = fields.Many2one('res.partner', 'Customer')
    related_meal = fields.Many2one('hotel.mealscount', 'Related Meals')


class hotel_date_select(models.TransientModel):
    _name = 'hotel.date_select'
    filter_date = fields.Date(string='Date', required=True, default=date.today())

    @api.multi
    def count_meals_daily(self):
        return {
            'name': 'Meals Report',
            'domain': [('meals_date', '=', self.filter_date)],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hotel.mealscount',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'date': self.filter_date}
        }
