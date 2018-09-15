from time import time
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from flask import render_template, redirect
from flask import request, url_for, abort, json
from flask.json import jsonify

from flask_login import login_required, current_user, login_user

from flask_sqlalchemy import Pagination

from . import api

from .. import db

from ..decorators import member_required

from ..models import ProductCategory, Product, Image, ProductImage
from ..models import Shoppoint
#from ..models import Shoppoint, Product, Address
#from ..models import Member, UserAuth
#from ..models import Ticket, TicketProduct, TicketAddress


@api.route('/categories/', methods=['GET'])
def categories():
    sp = Shoppoint.query.first_or_404()

    categories = ProductCategory.query.all()
    return jsonify([c.to_json() for c in categories])

@api.route('/<shopname>/products', methods=['GET'])
def products(shopname):
    sp = Shoppoint.query.filter_by(code=shopname).first_or_404()

    entities = [Product.id, Product.code, Product.name, Product.english_name, Product.price]

    #page = request.args.get('page', type=int, default=1)
    products = Product.query.filter_by(is_available_on_web=True, shoppoint_id=sp.id)#.with_entities(*entities)
    #pagination = products.paginate(page=page, per_page=7, error_out=False)
    #return render_template('api/list.html', products=products, shoppoint=sp, pagination=pagination)
    return jsonify([p.to_json() for p in products.all()])

@api.route('/<shopname>/product', methods=['GET', 'POST'])
def product(shopname):
    sp = Shoppoint.query.filter_by(code=shopname).first_or_404()
    if request.method == 'GET':
        code = request.args['code']
        p = Product.query.filter_by(code=code).first()

        return jsonify(p.to_json())
    elif request.method == 'POST':
        body = request.data.decode('utf-8') 
        data = json.loads(body)

        code = data.get('code')
        if code:
            product = Product.query.filter_by(code=code).first_or_404()
        else:
            product = Product()
            product.code = uuid4().hex
            db.session.add(product)
        product.shoppoint_id = sp.id
        product.shoppoint = sp
        product.original_price = float(data['original_price'])
        product.price = product.original_price
        product.member_price = float(data['member_price'])
        product.name = data['name']
        product.summary =  data['summary']
        product.description = data['note']
        product.size = data['size']
        product.english_name = data['english_name']

        photos = data['banner']
        photos.extend(data['photos'])
        #for photo in photos:
        #images = Image.query.filter(Image.id.in_(photos)).all()
        #pis = []
        print(photos)
        for o in photos:
            image = Image.query.get_or_404(o['code'])
            pi = None
            if code:
                pi = ProductImage.query.get((product.id, image.id))
            if not pi:
                pi = ProductImage()
                db.session.add(product)
            else:
                product.images = []

            pi.product_id = product.id
            pi.image_id = image.id
            pi.product = product
            pi.image = image
            pi.sequence = o['index']
            #pis.append(pi)
            product.images.append(pi)
            db.session.add(pi)

        db.session.commit()

        return jsonify(product.to_json()), 201
    else:
        abort(405)
    #ppc = {}
    #for pp in product.parameters:
    #    if pp.parameter.category not in ppc:
    #        ppc[pp.parameter.category] = [pp]
    #    else:
    #        ppc[pp.parameter.category].append(pp)
    #logger.debug(ppc)
    #message = request.args.get('added');
    #return render_template('api/detail.html', product=product, parameter_categories=ppc, message=message, shoppoint=sp)

@api.route('/product/spec/<code>', methods=['GET'])
def product_spec(code):
    sp = Shoppoint.query.first_or_404()
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
