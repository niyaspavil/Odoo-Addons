# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Logo change',
    'version': '9.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webcastle',
    'summary': 'change logo in the Point of Sale ',
    'description': """

=======================

This module allows to change logo in receipt.

""",
    'depends': ['pos_discount_fixed'],
    'data': [
        'views/templates.xml',
        'views/views.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
    'auto_install': False,
}
