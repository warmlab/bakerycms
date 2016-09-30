from datetime import datetime
from decimal import Decimal

from flask import render_template
from flask import request

from flask_login import login_required, current_user

from . import shop

from ..models import Product, ProductCategory
from ..models import Parameter, ParameterCategory, ProductParameter

"""
@shop.route('/products', methods=['GET'])
def product_list():
    products = Product.query.all()
    return render_template('shop/list.html', products=products)
"""

@shop.route('/product/<slug>', methods=['GET'])
def product_detail(slug):
    option_categories = ParameterCategory.query.all()
    product = Product.query.filter_by(code=slug).first()
    return render_template('shop/detail.html', product=product, option_categories=option_categories)

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
def checkout():
    # create an order to checkout
    to_buy_products = []
    to_buy_amounts = []
    total_cost = 0
    codes = request.form.getlist('product-code')
    amounts = request.form.getlist('amount')
    for code,amount in zip(codes,amounts):
        if request.form.get('-'.join(['is-buy', code])) == 'on':
            product = Product.query.filter_by(code=code).first()
            if product:
                to_buy_products.append(product)
                to_buy_amounts.append(amount)
                total_cost += product.price * int(amount)

    #products = Product.query.filter(Product.code.in_(to_buy_codes))
    #print('products: %s' % products)
    print('codes: %s, amounts: %s' % (to_buy_products, to_buy_amounts))
    now = datetime.utcnow()
    shoppoint_id = '9999'
    app_id = '2088711989941795'
    trade_number_format='%Y%m%d%H%M%S{0}%f'.format(shoppoint_id) 
    out_trade_no = now.strftime(trade_number_format)
    alipay_url = 'https://openapi.alipay.com/gateway.do'
    return render_template('shop/checkout.html', products=to_buy_products, amounts=to_buy_amounts, total_cost=total_cost)

@shop.route('/memberinfo', methods=['GET'])
def user_info():
    return render_template('shop/memberinfo.html')

@shop.route('/', methods=['GET', 'POST'])
def index():
    """
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)
    """
    products = Product.query.all()
    return render_template('shop/list.html', products=products)


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
