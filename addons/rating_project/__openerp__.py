# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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
##############################################################################

{
    'name': 'Project Rating',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
This module Allows a customer to give rating on Project.
""",
    'author': 'OpenERP SA',
    'website': 'http://openerp.com',
    'depends': [
        'rating',
        'project'
    ],
    'data': [
        'project_data.xml',
        'project_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
    'bootstrap': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
