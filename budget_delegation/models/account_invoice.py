# -*- coding: utf-8 -*-
# 
#    OpenERP, Open Source Management Solution

#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#

from openerp import models, fields, api, _
from datetime import datetime, timedelta

class AccountInvoice(models.Model):
    _inherit='account.invoice'

    delegation_id = fields.Many2one('res.delegation', 'Delegation')
    department_id = fields.Many2one('res.department', 'Department')
    section_id = fields.Many2one('res.section', 'Section')

    @api.multi
    def add_in_lines(self):
        for line in self.invoice_line_ids:
            line.delegation_id = self.delegation_id.id
            line.department_id = self.department_id.id
            line.section_id = self.section_id.id


class AccountInvoiceLine(models.Model):
    _inherit='account.invoice.line'

    delegation_id = fields.Many2one('res.delegation', 'Delegation')
    department_id = fields.Many2one('res.department', 'Department')
    section_id = fields.Many2one('res.section', 'Section')
