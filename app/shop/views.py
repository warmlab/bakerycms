from datetime import datetime
from decimal import Decimal

from flask import render_template, redirect
from flask import request, url_for, abort, json

from flask_login import login_required, current_user

from . import shop

from .. import db

from ..decorators import member_required

from ..models import Product, Member, Address
from ..models import Ticket, TicketProduct, TicketAddress

@shop.route('/products', methods=['GET'])
@shop.route('/', methods=['GET'])
def index():
    products = Product.query.filter_by(is_available_on_web=True)
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
    products = Product.query.filter_by(is_available_on_web=True)
    return render_template('shop/cart.html', products=products)

@shop.route('/checkout', methods=['POST']) # 结算
@login_required
@member_required
def checkout():
    # create an order to checkout
    items = []
    #amounts = request.form.getlist('amount')
    lines = request.form.getlist('product')
    amounts = request.form.getlist('amount')
    for line, amount in zip(lines, amounts):
        product_info = json.loads(line);
        tobuy = request.form.get('-'.join(['tobuy', str(product_info['code'])]))
        print(tobuy)
        if not tobuy:
            continue
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
        items.append((product, parameters, price, amount))

    return render_template('shop/pre-order.html', user=current_user, items=items)

@shop.route('/order', methods=['POST', 'GET'])
@login_required
@member_required
def order():
    if request.method == 'GET':
        code = request.args.get('order')
        if not code:
            abort(400)
        ticket = Ticket.query.get(code)
    elif request.method == 'POST':
        order_number_format = '%Y%m%d%H%M%S{0}%f'.format('0000') # the parameter is shoppoint code
        now = datetime.now()
        order_number = now.strftime(order_number_format)
        ticket = Ticket(code=order_number)
        print(order_number)
        # create an order to checkout
        total_price = Decimal(0)
        total_amount = 0
        #amounts = request.form.getlist('amount')
        product_codes = request.form.getlist('product')
        parameters_ids = request.form.getlist('parameter')
        amounts = request.form.getlist('amount')
        for code, para_ids, amount in zip(product_codes, parameters_ids, amounts):
            amount = Decimal(amount)
            product = Product.query.filter_by(code=code).first()
            price = product.price;
            parameters = []
            for para in product.parameters:
                if para.parameter_id in para_ids:
                    price += para.plus_price
                    parameters.append({"code": para.product_id, "name": para.parameter.name})
                    para_ids.remove(para.parameter_id)
            if para_ids:
                abort(400)

            tp = TicketProduct(product=product) 
            tp.parameters = json.dumps(parameters),
            tp.original_price = price
            tp.real_price = price
            tp.amount = amount
            ticket.products.append(tp)

            total_price += price * amount
            total_amount += amount

        ticket.required_datetime = now #request.form.get('date') + request.form.get('time')
        ticket.note = request.form.get('note')

        ticket.product_amount = total_amount
        ticket.original_price = total_price
        ticket.real_price = total_price
        ticket.member = current_user.member
        address = Address.query.get(request.form.get('target-location'))
        if address not in current_user.addresses:
            abort(400)
        else:
            ta = TicketAddress(contact_name=address.contact_name,
                    mobile=address.mobile, address=address.address)
            ticket.address = ta

    return render_template('shop/order.html', ticket=ticket, user=current_user)

@shop.route('/dopay', methods=['POST'])
def do_pay():
    return render_template('shop/payresult.html')

@shop.route('/wxpay', methods=['POST'])
def weixin_pay():
    return render_template('shop/payresult.html')

@shop.route('/payresult', methods=['POST', 'GET'])
def payresult():
    return render_template('shop/payresult.html')

@shop.route('/myshop', methods=['GET', 'POST'])
@login_required
@member_required
def myshop():
    tickets = Ticket.query.filter_by(member_id=current_user.member_id)
    return render_template('shop/myshop.html', tickets=tickets, user=current_user)

@shop.route('/myinfo', methods=['GET', 'POST'])
@login_required
def myinfo():
    if request.method == 'POST':
        mobile = request.form.get('loginmobile')
        email = request.form.get('loginemail')
        current_user.mobile = mobile
        current_user.email = email

        name = request.form.get('name')
        if current_user.member:
            current_user.member.name = name
        else:
            current_user.member = Member(name=name, mobile=mobile)
    return render_template('shop/myinfo.html', user=current_user)

@shop.route('/myaddress', methods=['GET', 'POST', 'DELETE', 'PUT'])
@login_required
@member_required
def my_address():
    if request.method == 'PUT':
        # new address
        info = json.loads(request.data)
        print(info['user'])
        print(current_user.id)
        if info['user'] != current_user.id:
            abort(400)
        address = Address(address=info['address'], contact_name=info['contact'], mobile=info['mobile'])
        current_user.addresses.append(address)
        db.session.add(address)
        db.session.commit()
        info = {'code': address.id}

        if 'application/json' in request.headers.get('Accept'):
            return json.dumps(info)
    elif request.method == 'DELETE':
        pass
    print (request.headers)
    print (request.data)
    return render_template('shop/myaddress.html', user=current_user)

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
