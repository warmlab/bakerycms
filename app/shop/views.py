from datetime import datetime
#from decimal import Decimal

from flask import render_template, redirect
from flask import request, url_for, abort, json

from flask_login import login_required, current_user

from . import shop

from .. import db

from ..decorators import member_required

from ..models import Product, Member

@shop.route('/products', methods=['GET'])
@shop.route('/', methods=['GET'])
def index():
    products = Product.query.filter_by(is_available_on_web=True).all()
    return render_template('shop/list.html', products=products)

@shop.route('/product/<code>', methods=['GET'])
def product_detail(code):
    product = Product.query.filter_by(code=code).first()
    ppc = {}
    for pp in product.parameters:
        if pp.parameter.category not in ppc:
            ppc[pp.parameter.category] = [pp]
        else:
            ppc[pp.parameter.category].append(pp)
    #logger.debug(ppc)
    message = request.args.get('added');
    return render_template('shop/detail.html', product=product, parameter_categories=ppc, message=message)

@shop.route('/add-to-cart', methods=['POST'])
@login_required
@member_required
def add_to_cart():
    code = request.form.get('code');
    if not code:
        abort(400)
    product = Product.query.filter_by(code=code).first()
    parameters = request.form.getlist('parameters')
    item = ShoppingCart(current_user, product, parameters)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('.product_detail', code=code, added=True, _method='GET'));

@shop.route('/cart', methods=['GET'])
def cart():
    products = Product.query.all()
    return render_template('shop/cart.html', products=products)

@shop.route('/dopay', methods=['POST'])
def do_pay():
    return render_template('shop/payresult.html')

@shop.route('/wxpay', methods=['POST'])
def weixin_pay():
    return render_template('shop/payresult.html')

@shop.route('/payresult', methods=['POST', 'GET'])
def payresult():
    return render_template('shop/payresult.html')

@shop.route('/checkout', methods=['POST'])
@login_required
@member_required
def checkout():
    # create an order to checkout
    total_cost = 0
    items = []
    #amounts = request.form.getlist('amount')
    lines = request.form.getlist('product')
    for line in lines:
        product_info = json.loads(line);
        parameters_info = json.loads(product_info.get('parameters'))
        parameters_info = [p['code'] for p in parameters_info]

        product = Product.query.filter_by(code=product_info['code']).first()

        price = product.price;
        parameters = []
        for para in product.parameters:
            if para.parameter_id in parameters_info:
                price += para.plus_price
                parameters.append(para)
                parameters_info.remove(para.parameter_id)
        if parameters_info:
            abort(400)
        items.append((product, parameters, price, product_info['amount']))
        total_cost += price * product_info['amount']

        #if request.form.get('-'.join(['is-buy', code])) == 'on':
        #    product = Product.query.filter_by(code=code).first()
        #    if product:
        #        to_buy_products.append(product)
        #        to_buy_amounts.append(amount)
        #        total_cost += product.price * int(amount)

    member = current_user.member
    #print(member)
    #if not member:
    #    # redirect member info page
    #    return redirect(url_for('.member_info', next=url_for('.cart'), _method='GET'))
    #items = Product.query.filter(Product.code.in_(to_buy_codes))
    #print('items: %s' % items)
    #print('codes: %s, amounts: %s' % (to_buy_products, to_buy_amounts))
    now = datetime.utcnow()
    shoppoint_id = '9999'
    #app_id = '2088711989941795'
    trade_number_format='%Y%m%d%H%M%S{0}%f'.format(shoppoint_id) 
    #out_trade_no = now.strftime(trade_number_format)
    #alipay_url = 'https://openapi.alipay.com/gateway.do'
    return render_template('shop/checkout.html', items=items, total_cost=total_cost)

@shop.route('/myinfo', methods=['GET', 'POST'])
@login_required
def member_info():
    if request.method == 'POST':
        name = request.form.get('inputname')
        current_user.member = Member(name=name)
        db.session.add(current_user.member)
        db.session.commit()
    return render_template('shop/myinfo.html', user=current_user)

@shop.route('/member/<username>')
def user(username):
    user = Member.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@shop.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@shop.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
#@admin_required
def edit_profile_admin(id):
    user = Member.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
