from decimal import Decimal

from flask import render_template
from flask import request

from . import sale
from flask_login import login_required, current_user

from ..models import Product, ProductCategory
from ..models import Parameter, ParameterCategory, ProductParameter

from ..decorators import staff_required

@sale.route('/sale/', methods=['GET'])
@sale.route('/sale/summary', methods=['GET'])
@login_required
@staff_required
def summary():
    tickets = []
    return render_template('sale/summary.html', tickets=tickets)

@sale.route('/sale/tickets', methods=['GET'])
@login_required
@staff_required
def sale_tickets():
    return render_template('sale/tikcets.html')

@sale.route('/sale/ticket', methods=['GET', 'POST'])
@login_required
@staff_required
def sale_ticket():
    ticket = None
    return render_template('sale/detail.html', ticket=ticket)
