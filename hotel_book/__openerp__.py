{
    'name': 'Hotel Education Management System',
    'version': '1.0',
    'author': 'Webcastle',
    'sequence': 2,
    'category': 'Hotel Education Management',
    'summary': 'Management of booking Rooms of particular type, Meals and Events',
    'description': """
This module is used by :

- Rooms Booking
- Meals Booking
- Events Registration

Manage rental schedule, bookings, arrivals and departure.

Use it with its WebSite App and allow your customers to book rooms, meals and event participation !

""",
    'depends': ['base', 'sale', 'account_accountant',
                'stock', 'event', 'payment', 'product', 'payment_paypal', 'payment_ogone',
                'event_sale', 'web_m2x_options','base_vat',
                ],
    'data': [
        'security/ir.model.access.csv',
        'hotel_book_view.xml',
        'hotel_customer_view.xml',
        'hote_document_view.xml',
        'hotel_category_view.xml',
        'hotel_room_view.xml',
        'hotel_workflow.xml',
        'hotel_meals_view.xml',
        'hotel_sequence.xml',
        'hotel_amenities_view.xml',
        'hotel_services_view.xml',
        'hotel_order_view.xml',
        'hotel_others_view.xml',
        'hotel_payment_acquirer_view.xml',
        'hotel_advance_pay_view.xml',
        'hotel_voucher_view.xml',
        'hotel_report.xml',
        'room_summ_view.xml',
        'hote_meals_today_view.xml',
        'views/book_report_view.xml',
        'views/folio_report_view.xml',
        'hotel_reservation_summary.xml',
    ],
    'js': ["static/src/js/hotel_room_reservation_summary.js", ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,

}
