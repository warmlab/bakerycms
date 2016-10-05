from decimal import Decimal

from flask import render_template
from flask import request

from . import sale
from flask_login import login_required, current_user

from ..models import Product, ProductCategory
from ..models import Parameter, ParameterCategory, ProductParameter

@sale.route('/sale/', methods=['GET'])
@sale.route('/sale/summary', methods=['GET'])
@login_required
def summary():
    tickets = []
    return render_template('sale/summary.html', tickets=tickets)

@sale.route('/sale/tickets', methods=['GET'])
@login_required
def sale_tickets():
    return render_template('sale/tikcets.html')

@sale.route('/sale/ticket', methods=['GET', 'POST'])
@login_required
def sale_ticket():
    return render_template('sale/detail.html', ticket=ticket)
