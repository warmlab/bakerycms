from time import time
from datetime import datetime
from decimal import Decimal

from flask import render_template, redirect
from flask import request, url_for, abort, json

from flask_login import login_required, current_user, login_user

from flask_sqlalchemy import Pagination

from . import shop

from .. import db

from ..decorators import member_required

from ..models import Shoppoint, Product, Address
from ..models import Member, UserAuth
from ..models import Ticket, TicketProduct, TicketAddress

from ..weixin import pay as weixin_pay
from ..weixin import access as weixin_access


@shop.route('/products', methods=['GET'])
@shop.route('/', methods=['GET'])
def index():
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)

    page = request.args.get('page', type=int, default=1)
    products = Product.query.filter_by(is_available_on_web=True)
    pagination = products.paginate(page=page, per_page=7, error_out=False)
    return render_template('shop/list.html', products=products, shoppoint=sp, pagination=pagination)

@shop.route('/product/<code>', methods=['GET'])
def product_detail(code):
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)
    product = Product.query.filter_by(code=code).first()
    ppc = {}
    for pp in product.parameters:
        if pp.parameter.category not in ppc:
            ppc[pp.parameter.category] = [pp]
        else:
            ppc[pp.parameter.category].append(pp)
    #logger.debug(ppc)
    message = request.args.get('added');
    return render_template('shop/detail.html', product=product, parameter_categories=ppc, message=message, shoppoint=sp)

def _get_userinfo_from_weixin(weixin_code):
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)
    if weixin_code:
        params = [('appid', sp.weixin_appid),
                  ('secret', sp.weixin_appsecret),
                  ('code', weixin_code),
                  ('grant_type', 'authorization_code')
                ]
        # get access token
        token_info = weixin_access.access_weixin_api('https://api.weixin.qq.com/sns/oauth2/access_token', params)
        if 'errcode' in token_info:
            return  None
        access_token = token_info.get('access_token')
        expires_in = token_info.get('expires_in')
        openid = token_info.get('openid')
        refresh_token = token_info.get('refresh_token')
        #scope = info.get('scope')
        member = Member.query.filter_by(weixin_openid=openid).first()
        if not member:
                ## refresh access token
                #params = [('appid', sp.weixin_appid),
                #          ('grant_type', 'refresh_token'),
                #          ('refresh_token', token_info.get('refresh_token'))
                #        ]
                #token_info = weixin_access.access_weixin_api('https://api.weixin.qq.com/sns/oauth2/refresh_token', params)
            member = Member()
            user = UserAuth(member=member, active=True, confirmed_at=datetime.utcnow())
        else:
            user = UserAuth.query.filter_by(member_id=member.id).first()
        member.weixin_openid=openid
        member.weixin_token=access_token
        member.weixin_expires_time=int(time()) + expires_in - 5
        member.weixin_refresh_token=refresh_token

        # get user info from weixin
        params = [('access_token', token_info.get('access_token')),
                  ('openid', token_info.get('openid')),
                  ('lang', 'zh_CN')
                 ]
        user_info = weixin_access.access_weixin_api('https://api.weixin.qq.com/sns/userinfo', params)
        member.nickname = user_info.get('nickname')
        member.gender = user_info.get('sex')
        member.weixin_unionid = user_info.get('unionid')
        member.headimgurl = user_info.get('headimgurl')

        # TODO create a random passcode
        user.password = uuid4().hex
        db.session.add(member)
        db.session.add(user)
        db.session.commit()

        return user

@shop.route('/cart', methods=['GET'])
def cart():
    #products = Product.query.filter_by(is_available_on_web=True)
    weixin_code = request.args.get('code')
    #if not weixin_code:
    #    params = [('appid', sp.weixin_appid),
    #              ('redirect_uri', url_for('.cart', _external=True)),
    #              ('response_type', 'code'),
    #              ('scope', 'snsapi_userinfo')
    #            ]
    #    url = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    #    url = '?'.join([url, urlparse.urlencode(params)])
    #    url = '#'.join([url, 'wechat_redirect'])
    #    print(url)
    #    return redirect(url)
    user = _get_userinfo_from_weixin(weixin_code)
    # login to system
    print('in shoppoint cart ', user)
    r = login_user(user)
    print('login result: ', r)

    return render_template('shop/cart.html', weixin_user=user)

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

@shop.route('/order/', methods=['POST', 'GET'])
@login_required
@member_required
def order():
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)
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

    weixin = weixin_pay.unified_order_js_config(sp.weixin_appid, sp.weixin_appsecret)
    return render_template('shop/order.html', ticket=ticket, user=current_user, weixin=weixin)

@shop.route('/unifiedorder', methods=['POST'])
@login_required
@member_required
def unified_order():
    sp = Shoppoint.query.first()
    if not sp:
        abort(404)
    ticket_code = request.form.get('ticket-code')
    ticket = Ticket.query.get(ticket_code)
    result = weixin_pay.unified_order(ticket, sp.weixin_appid,
            sp.weixin_mchid, sp.weixin_appsecret,
            current_user, url_for('weixin.pay_notify', _external=True))

    if result.get('return_code') == "SUCCESS":
        if result.get('result_code') == "SUCCESS":
            ticket.payment_code = result.get('prepay_id')
            package = '='.join(['prepay_id', result.get('prepay_id')])
            params = {'timeStamp': int(time()), 'appId': sp.weixin_appid, 'nonceStr': result.get('nonce_str'), 'package': package, 'signType': 'MD5'}
            params['signature'], signType = weixin_pay.generate_sign(params, sp.weixin_appsecret)
            params['pack'] = [package]

            return json.dumps(params), 201
        elif result.get('result_code') == 'FAIL' and result.get('err_code') == 'OUT_TRADE_NO_USED':
            return result, 409
    return '{"error-code": 1, "errMsg": "error"}', 403 # TODO

@shop.route('/dopay', methods=['POST'])
def do_pay():
    return render_template('shop/payresult.html')

@shop.route('/payresult', methods=['POST', 'GET'])
def payresult():
    return render_template('shop/payresult.html')

@shop.route('/myshop', methods=['GET'])
@login_required
@member_required
def myshop():
    if not current_user.is_anonymous:
        tickets = Ticket.query.filter_by(member_id=current_user.member_id)
        return render_template('shop/myshop.html', tickets=tickets, user=current_user)
    else:
        return redirect(url_for('auth.login'))

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

from ..models import BakeryClass
@shop.route('/class')
def diy():
    #return redirect('https://mp.weixin.qq.com/s?__biz=MzAwMjE3MzEyNw==&mid=2455220715&idx=1&sn=d0798bb8779fd9dec89f9958017f249b&chksm=8d6d6043ba1ae9551cdc202ce9bbd2040fe18f950096a8f26eda4d2345bbedb17cd1e7ef3bbd&mpshare=1&scene=1&srcid=1123XB5W4s9PqTG1KAS8WxtG&pass_ticket=0Y41Ml3EcPHX%2B%2FVBw5imdigDDp8ejLPhVIR%2Fj7DUZlr0jaLe7oh9G6Q404U66%2BEN#rd')
    return redirect('https://mp.weixin.qq.com/s?__biz=MzAwMjE3MzEyNw==&mid=2455220732&idx=1&sn=42f816f59e2e6fc3b01078e59612ca47&pass_ticket=hibJGWHAmwSe%2BaA76YYeyTQRqpBY%2Fzo%2B6HCCr8s9utveCV2TJFOuU6dVGMNJauP2')
    #bakery_class = BakeryClass.query.first()

    #return render_template('class/detail.html', bakery_class=bakery_class)

from ..models import Bakery
from uuid import uuid4

@shop.route('/class/book', methods=['POST'])
def book_class():
    name = request.form.get('name')
    mobile = request.form.get('mobile')

    if not name or not mobile:
        abort(400)

    userauth = UserAuth.query.filter_by(mobile=mobile).first()
    if not userauth:
        member = Member(name=name, mobile=mobile)
        userauth = UserAuth(mobile=mobile, active=True, confirmed_at=datetime.utcnow())
        userauth.password = uuid4().hex
    elif not userauth.member:
        member = Member(name=name, mobile=mobile)
        userauth.member = member
    bakery_class = BakeryClass.query.get(request.form.get('bakery-class-code'))
    if not bakery_class:
        abort(404)

    bakery = Bakery.query.filter_by(userauth_id=userauth.id, bakery_class_id=bakery_class.id).first()
    if bakery:
        return render_template('class/already_booked.html', bakery=bakery)

    #member = Member(name=name, mobile=mobile)
    #userauth = UserAuth(mobile=mobile, active=True, confirmed_at=datetime.utcnow(), member=member)
    if bakery_class:
        bakery = Bakery(bakery_class=bakery_class, member=userauth)
        return render_template('class/succeed_booking.html', bakery=bakery)
