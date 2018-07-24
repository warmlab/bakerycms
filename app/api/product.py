from time import time
from datetime import datetime
from decimal import Decimal

from flask import render_template, redirect
from flask import request, url_for, abort, json
from flask.json import jsonify

from flask_login import login_required, current_user, login_user

from flask_sqlalchemy import Pagination

from . import api

from .. import db

from ..decorators import member_required

from ..models import ProductCategory, Product
from ..models import Shoppoint
#from ..models import Shoppoint, Product, Address
#from ..models import Member, UserAuth
#from ..models import Ticket, TicketProduct, TicketAddress


@api.route('/categories/', methods=['GET'])
def categories():
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)

    categories = ProductCategory.query.all()
    return jsonify([c.to_json() for c in categories])

@api.route('/<shopname>/products', methods=['GET'])
def products(shopname):
    sp = Shoppoint.query.filter_by(name=shopname)
    if not sp:
        abort(404)

    entities = [Product.id, Product.code, Product.name, Product.english_name, Product.price]

    #page = request.args.get('page', type=int, default=1)
    products = Product.query.filter_by(is_available_on_web=True)#.with_entities(*entities)
    #pagination = products.paginate(page=page, per_page=7, error_out=False)
    #return render_template('api/list.html', products=products, shoppoint=sp, pagination=pagination)
    return jsonify([p.to_json() for p in products.all()])

@api.route('/<shopname>/product/<code>', methods=['GET'])
def product(shopname, code):
    sp = Shoppoint.query.filter_by(name=shopname)
    if not sp:
        abort(404)
    #code = 1
    p = Product.query.filter_by(code=code).first()
    #ppc = {}
    #for pp in product.parameters:
    #    if pp.parameter.category not in ppc:
    #        ppc[pp.parameter.category] = [pp]
    #    else:
    #        ppc[pp.parameter.category].append(pp)
    #logger.debug(ppc)
    #message = request.args.get('added');
    #return render_template('api/detail.html', product=product, parameter_categories=ppc, message=message, shoppoint=sp)
    return jsonify(p.to_json())

@api.route('/product/spec/<code>', methods=['GET'])
def product_spec(code):
    sp = Shoppoint.query.first()
    if not sp:
        about(404)

    ppc = {}
    product = Product.query.filter_by(code=code).first()
    for pp in product.parameters:
        if pp.parameter.category not in ppc:
            ppc[pp.parameter.category.name] = [pp.to_json()]
        else:
            ppc[pp.parameter.category.name].append(pp.to_json())

    #return jsonify([p.to_json() for p in c for c in ppc])
    return jsonify(ppc)
