from decimal import Decimal

from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response

from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries

from .. import db
from . import product # blueprint

#from application import app

from ..models import Product, ProductCategory#, Specification
from ..models import Parameter, ParameterCategory, ProductParameter
from ..models import Member
from ..models import Image, ProductImage

from ..decorators import admin_required, permission_required


@product.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['CARO_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


# If GET is present, HEAD will be added automatically for you
@product.route('/products', methods=['GET', 'POST'])
def product_list():
    products = Product.query.all()
    return render_template('product/list.html', products=products)

def _product_images(product, image_names):
    print(image_names)
    pis = product.images
    found_image = []
    for name in image_names:
        #pi = ProductImage.query.filter_by(product=product, image=image)
        found = False
        for tpi in pis:
            if tpi.image.name == name:
                found = True
                found_image.append(tpi)

        if not found:
            image = Image.query.filter_by(name=name).first()
            pi = ProductImage(product, image)
            product.images.append(pi)

            db.session.add(pi)

    # delete image
    for pi in pis:
        if pi not in found_image:
            product.images.remove(pi)
            #db.session.delete(pi)

def _product_parameters(product, pc, parameters, price_parameter_values, stock_parameter_values):
    print("product parameters: %s" % (parameters))
    all_parameters = [o.id for o in pc.parameters]
    defined_parameters = []
    for po in product.parameters:
        if po.parameter.parameter_category_id == pc.id:
            defined_parameters.append(po.parameter_id)
    print (defined_parameters)

    #all_parameters = [str(po.parameter_id) for po in product.parameters]
    for o,v,s in zip(parameters, price_parameter_values, stock_parameter_values):
        o = int(o)
        parameter = Parameter.query.get_or_404(o)
        print ('ooooooooooo: ', o)
        if o in defined_parameters:
            print ('ooooooooooo: ', o in defined_parameters)
            po = ProductParameter.query.get_or_404((product.id, parameter.id))
            po.price = Decimal(v)
            po.stock = Decimal(s)
            defined_parameters.remove(o)
        else:
            po = ProductParameter(product, parameter, Decimal(v), Decimal(s))
            product.parameters.append(po)
        db.session.add(po)
    for o in defined_parameters:
        parameter = Parameter.query.get_or_404(o)
        po = ProductParameter.query.get_or_404((product.id, parameter.id))
        product.parameters.remove(po)
        db.session.delete(po)

@product.route('/product/<slug>', methods=['GET', 'POST'])
def product_detail(slug):
    if request.method == 'GET':
        if slug == 'new-product':
            product = None
        else:
            product = Product.query.filter_by(code=slug).first()
        categories = ProductCategory.query.all()
        parameter_categories = ParameterCategory.query.all()
        images = Image.query.all()
        #specifications = Specification.query.all()
        #parameters = Parameter.query.all()

        return render_template('product/detail.html', product=product, categories=categories,
                               parameter_categories=parameter_categories, images=images)
    elif request.method == 'POST':
        print("the slug is: %s" % slug)
        if request.form.get('checkweb'):
            checkweb = True
        else:
            checkweb = False
        if request.form.get('checkpos'):
            checkpos = True
        else:
            checkpos = False
        if request.form.get('checkpoint'):
            checkpoint = True
        else:
            checkpoint = False
        if slug == 'new-product':
            category_id = request.form['categoryparameter'] # 产品分类
            category = ProductCategory.query.get_or_404(category_id)
            product = Product(request.form['inputcode'], request.form['inputname'], request.form['inputenglishname'],
                              request.form['inputpinyin'], category, request.form['inputoriginalprice'],
                              request.form['inputprice'], request.form['inputmemberprice'], request.form['inputstock'],
                              checkweb, checkpos, checkpoint)
            print ("The new product is: %s" % product)
        if request.form['inputcode'] != slug:
            return render_template('404.html')
        else:
            product = Product.query.filter_by(code=slug).first()
            print ("The product is: %s" % product)

            product.name = request.form['inputname']
            product.english_name = request.form['inputenglishname']
            product.pinyin = request.form['inputpinyin']
            category_id = request.form['categoryparameter'] # 产品分类
            product.category = ProductCategory.query.get_or_404(category_id)
            product.original_price = request.form['inputoriginalprice']
            product.price = request.form['inputprice']
            product.member_price = request.form['inputmemberprice']
            product.stock = request.form['inputstock']
            product.is_available_on_web = checkweb
            product.is_available_on_pos = checkpos
            product.is_deleted = False
            product.to_point = checkpoint
            #categories = ProductCategory.query.get_or_404()

        # set product images
        image_names = request.form.getlist('product-image')
        _product_images(product, image_names)

        # set product parameters
        for pc in ParameterCategory.query.all():
            parameters = request.form.getlist('-'.join(['parameter', str(pc.id)]))
            price_parameter_values = request.form.getlist('-'.join(['inputparameter', str(pc.id), 'price']))
            stock_parameter_values = request.form.getlist('-'.join(['inputparameter', str(pc.id), 'stock']))
            _product_parameters(product, pc, parameters, price_parameter_values, stock_parameter_values)

        removed_parameters = []

        # save product to database
        db.session.add(product)
        db.session.commit()

        product = Product.query.filter_by(code=slug).first()
        categories = ProductCategory.query.all()
        parameter_categories = ParameterCategory.query.all()
        parameters = Parameter.query.all()
        images = Image.query.all()

        return render_template('product/detail.html', product=product, categories=categories,
                           parameter_categories=parameter_categories, parameters=parameters, images=images)
    else:
        return render_template('method_not_allowed.html')

@product.route('/categories', methods=['GET', 'POST'])
def category_list():
    categories = ProductCategory.query.all()
    return render_template('category/list.html', categories=categories)


@product.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
