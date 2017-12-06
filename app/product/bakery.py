from decimal import Decimal

from flask import render_template, redirect, url_for, abort, request,\
    current_app #, make_response

from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries

from .. import db
#from . import bakery # blueprint
from . import product

#from application import app

from ..models import BakeryClass, Bakery, BakeryCategory#, Specification
#from ..models import Staff
from ..models import Image, BakeryImage

from ..decorators import staff_required


@product.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['BAKERY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response

# If GET is present, HEAD will be added automatically for you
@product.route('/bakery/classes', methods=['GET'])
@login_required
@staff_required
def class_list():
    bakery_classes = BakeryClass.query
    return render_template('bakery/list.html', bakery_classes=bakery_classes)

def _bakery_images(bakery, image_names):
    pis = bakery.images
    found_images = []
    to_append_images = []
    for name in image_names:
        #pi = ProductImage.query.filter_by(bakery=bakery, image=image)
        found = False
        for tpi in pis:
            if tpi.image.name == name:
                found = True
                found_images.append(tpi)

        if not found:
            to_append_images.append(name)

    # delete image
    for pi in pis:
        if pi not in found_images:
            print('delete pi: ', pi.product_id)
            db.session.delete(pi)
            bakery.images.remove(pi)

    # append added images
    for name in to_append_images:
        image = Image.query.filter_by(name=name).first()
        pi = ProductImage(bakery=bakery, image=image)
        bakery.images.append(pi)

def _bakery_times(bakery, class_times):
    print("bakery parameters: %s" % class_times)

@product.route('/bakery/class', methods=['GET', 'POST'])
@login_required
@staff_required
def bakery_detail():
    create = request.args.get('new')
    if request.method == 'POST':
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
        if create == '1':
            category_id = request.form['categoryparameter'] # 烘焙课程分类
            category = BakeryCategory.query.get_or_404(category_id)
            bakery = Bakery(code=request.form['inputcode'], name=request.form['inputname'], english_name=request.form['inputenglishname'],
                              pinyin=request.form['inputpinyin'], category=category, original_price=Decimal(request.form['inputoriginalprice']),
                              price=Decimal(request.form['inputprice']), member_price=Decimal(request.form['inputmemberprice']), stock=Decimal(request.form['inputstock']),
                              is_available_on_web=checkweb, is_available_on_pos=checkpos, to_point=checkpoint)
            bakery.description = request.form.get('inputdesc')
            print ("The new bakery is: %s" % bakery)
        else:
            code = request.args.get('code')
            if not code:
                abort(400)
            bakery = Bakery.query.filter_by(code=code).first()
            print ("The bakery is: %s" % bakery)

            bakery.name = request.form['inputname']
            bakery.english_name = request.form['inputenglishname']
            bakery.pinyin = request.form['inputpinyin']
            category_id = request.form['categoryparameter'] # 产品分类
            bakery.category = BakeryCategory.query.get_or_404(category_id)
            bakery.original_price = request.form['inputoriginalprice']
            bakery.price = request.form['inputprice']
            bakery.member_price = request.form['inputmemberprice']
            bakery.stock = request.form['inputstock']
            bakery.is_available_on_web = checkweb
            bakery.is_available_on_pos = checkpos
            bakery.is_deleted = False
            bakery.to_point = checkpoint
            bakery.description = request.form.get('inputdesc')
            #categories = BakeryCategory.query.get_or_404()

        # set bakery images
        image_names = request.form.getlist('bakery-image')
        _bakery_images(bakery, image_names)

        # save bakery to database
        #db.session.add(bakery)
        #db.session.commit()

        #bakery = Bakery.query.filter_by(code=slug).first()
        #categories = BakeryCategory.query.all()
        #parameter_categories = ParameterCategory.query.all()
        #parameters = Parameter.query.all()
        #images = Image.query.all()

        #return render_template('bakery/detail.html', bakery=bakery, categories=categories,
        #                   parameter_categories=parameter_categories, parameters=parameters, images=images)
        return redirect(url_for('.product_list'))
    if create == '1':
        bakery = None
    else:
        code = request.args.get('code')
        if not code:
            abort(400)
        bakery = Bakery.query.filter_by(code=code).first()
    categories = BakeryCategory.query
    images = Image.query
    #specifications = Specification.query.all()
    #parameters = Parameter.query.all()

    return render_template('bakery/detail.html', bakery=bakery, categories=categories,
                           images=images)

@product.route('/bakery/categories', methods=['GET'])
@login_required
@staff_required
def bakery_category_list():
    categories = BakeryCategory.query
    return render_template('bakery/category_list.html', categories=categories)

@product.route('/bakery/category', methods=['GET', 'POST'])
@login_required
@staff_required
def bakery_category_detail():
    create = request.args.get('new')
    if request.method == 'POST':
        name = request.form.get('inputname')
        english_name = request.form.get('inputenglishname')
        desc = request.form.get('inputdesc')
        if create:
            category = BakeryCategory(name, english_name, desc)
        else:
            pk = request.args.get('code')
            category = BakeryCategory.query.get(pk)
            category.name = name
            category.english_name = english_name
            category.description = desc
        db.session.add(category)
        db.session.commit()
        #return render_template('category/list.html', category=category)
        return redirect(url_for('.category_list'))

    if create == "1":
        return render_template('category/detail.html', category=None)
    else:
        pk = request.args.get("code")
        if not pk:
            abort(400)
        category = BakeryCategory.query.get(pk)
        return render_template('category/detail.html', category=category)
