#import urllib
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.request import Request
#from urllib import request as url_request

from datetime import datetime
from time import time
from uuid import uuid4

from flask import json, jsonify, abort
from flask import request, url_for
from flask.json import jsonify

from . import api
from .. import db

from ..models import Dragon, DragonProduct, DragonAddress, DragonOrder, DragonOrderProduct
from ..models import Product, Shoppoint
from ..models import MemberOpenID, Member, DeliveryAddress

from .wechat import unified_order, generate_pay_sign

@api.route('/<shop>/dragon/login', methods=['POST'])
def dragon_login(shop):
    j = json.loads(request.data.decode('utf-8'))
    #code = request.args['code']
    print(j)
    code = j['code']

    sp = Shoppoint.query.filter_by(code=shop).first_or_404()

    data = (
        ('appid', sp.weixin_mini_appid),
        ('secret', sp.weixin_mini_appsecret),
        ('js_code', code),
        ('grant_type', 'authorization_code')
    )

    r = Request('https://api.weixin.qq.com/sns/jscode2session?'+urlencode(data), method='GET')
    with urlopen(r) as s:
        result = s.read().decode('utf-8')
        info = json.loads(result)
        if 'errcode' in info:
            return jsonify(info), 400

        mo = MemberOpenID.query.filter_by(openid=info['openid']).first()
        if not mo:
            mo = MemberOpenID()
            mo.openid = info['openid']

        mo.session_key = info['session_key']
        #mo.expires_time = int(time()) + info['expires_in'] - 5
        #mo.generate_session_key = uuid4().hex

        if 'unionid' in info and not mo.unionid:
            mo.unionid = info['unionid']
            m = Member.query.filter_by(unionid=mo.unionid).first()
            if m:
                mo.member = m

        mo.save()

        return jsonify(mo.to_json())

    abort(403)

@api.route('/<shop>/dragon/auth', methods=['POST'])
def dragon_auth(shop):
    j = json.loads(request.data.decode('utf-8'))
    openid = j['openid']

    need = j['need'] # need privilege

    mo = MemberOpenID.query.filter_by(openid=openid).first_or_404()

    if mo.privilege & 1 and need == 'create': # need a function to do this
        return jsonify({
            'errcode': 200,
            'errmsg': 'you are allowed to create dragons'
            }), 200

    return jsonify({
        'errcode': 403,
        'errmsg': 'you are NOT allowed to create dragons'
        }), 403


@api.route('/<shop>/dragon/info', methods=['GET'])
def dragon_info(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()

    code = request.args.get('code')
    if not code:
        abort(400)

    #today = datetime.now()
    dragon = Dragon.query.get_or_404(code)

    return jsonify(dragon.to_json())


@api.route('/<shop>/dragon/addresses', methods=['GET'])
def addresses(shop):
    addresses = DragonAddress.query.all()

    return jsonify([a.to_json() for a in addresses])

@api.route('/<shop>/dragon/address_new', methods=['PUT'])
def address_new(shop):
    if request.method != 'PUT':
        return "Method not allowed", 405

    data = request.data.decode('utf-8')

    d = json.loads(data)
    address = DragonAddress(**d)
    #if d["is_default"]:
    #    DragonAddress.query.update({"is_default":False})
    address.save()
    
    return jsonify(address.to_json()), 201


@api.route('/<shop>/dragon/new', methods=['POST'])
def dragon_new(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()

    data = json.loads(request.data.decode('utf-8'))
    print(data)

    #products = Product.query.filter(Product.code.in_([p.code for p in data['products'])).all()
    addresses = DragonAddress.query.filter(DragonAddress.id.in_(data['addrs_sel'])).all()

    #dragon = Dragon('dragon', data['products'], data['products_bind'], data['member_allowed'], addresses, data['from_date'], data['from_time'], data['to_date'], data['to_time'], data['publish'], data['publish_date'], data['publish_time'])
    dragon = Dragon('dragon', data['openid'])
    dragon.bind_flag = data['products_bind']
    dragon.member_flag = data['member_allowed']
    #dragon.addresses = [dragon_address_relation(dragon.id, a.id) for a in addresses]
    dragon.addresses = addresses
    dragon.from_time = datetime.strptime(
            ' '.join([data['from_date'], data['from_time']]), '%Y-%m-%d %H:%M')
    dragon.to_time = datetime.strptime(' '.join([data['to_date'], data['to_time']]), '%Y-%m-%d %H:%M')
    dragon.last_order_time = datetime.strptime(' '.join([data['last_order_date'], data['last_order_time']]), '%Y-%m-%d %H:%M')
    dragon.shoppoint_id = sp.id
    dragon.shoppoint = sp
    if data['publish']:
        dragon.publish_time = datetime.strptime(' '.join([data['publish_date'], data['publish_time']]), '%Y-%m-%d %H:%M')
    else:
        dragon.publish_time = datetime.now()

    dragon.products = []
    
    for p in data['products']:
        product = Product.query.filter_by(code=p['code'], shoppoint_id=sp.id).first_or_404()
        dp = DragonProduct(dragon.id, product.id)
        dp.price = p['price']
        dp.total = p['amount']
        dragon.products.append(dp)
    dragon.delivery_fee = 0 if data['delivery_method'] == "0" else data['delivery_fee']

    dragon.description = data['note']
    dragon.delivery_method = data['delivery_method']
    dragon.prepay_flag = data['prepay_flag']

    dragon.save()

    return jsonify(dragon.to_json()), 201

@api.route('/<shop>/dragon/remove', methods=['PUT'])
def dragon_remove(shop):
    data = request.data.decode('utf-8')

    dragon = Dragon.query.get_or_404(int(data))
    dragon.remove()

    return jsonify({
        'errcode': 201,
        'errmsg': 'the dragon ' + data + ' was removed successfully'
        }), 201


@api.route('/<shop>/dragons', methods=['GET'])
def dragon_list(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()
    openid = request.args.get('openid')
    print('openid', openid)
    mo = MemberOpenID.query.filter_by(openid=openid).first_or_404()
    if not (mo.privilege & 1):
        return jsonify({
            'errcode': 403,
            'errmsg': 'You are not allowed to manage dragons, please contact with adminstrator'
            }), 403

    dragons = Dragon.query.filter_by(owner_id=mo.id, shoppoint_id=sp.id).order_by(Dragon.publish_time.desc()).all()

    return jsonify([d.to_json() for d in dragons])


@api.route('/<shop>/dragon/latest', methods=['GET'])
def dragon_latest(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()
    already_join = False
    today = datetime.now()

    dragon = Dragon.query.filter(Dragon.publish_time<=today, Dragon.to_time>=today, Dragon.shoppoint_id==sp.id)\
                        .order_by(Dragon.publish_time.desc()).first_or_404()

    #openid = request.args.get('openid')
    #print(request.args)
    #if openid:
    #    mo = MemberOpenID.query.filter_by(openid=openid).first()
    #    if mo:
    #        do = DragonOrder.query.filter_by(dragon_id=dragon.id, member_id=mo.id).first()
    #        if do: # already join this dragon
    #            already_join = True

    d = dragon.to_json()
    #d['already_join'] = already_join
    return jsonify(d)

@api.route('/<shop>/dragon/join/info', methods=['GET'])
def dragon_join_info(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()

    code = request.args.get('code')
    openid = request.args.get('openid')
    if not code or not openid:
        abort(400)

    dragon = Dragon.query.get_or_404(code)
    member = MemberOpenID.query.filter_by(openid=openid).first_or_404()

    order = DragonOrder.query.filter_by(dragon_id=dragon.id,
                                        member_id=member.id).first()

    return jsonify({
        'dragon': dragon.to_json(),
        'order': None if not order else order.to_json()
        })

@api.route('/<shop>/dragon/orders', methods=['GET'])
def dragon_orders(shop):
    dragon_id = request.args['key']
    dragon = Dragon.query.get_or_404(dragon_id)
    d = [do.to_json() for do in dragon.orders]
    print(d)

    return  jsonify(d)

def _get_next_seq(dragon_id):
    # get next seq
    next_seq = db.session.query(db.func.max(DragonOrder.seq)).scalar()
    if next_seq:
        next_seq += 1
    else:
        next_seq = 1

    if next_seq % 10 == 4 or next_seq == 250:
        next_seq += 1

    return next_seq

def join_dragon(shop, data):
    # create or get the order info
    if 'openid' not in data:
        return jsonify({
            'errcode': 400,
            'errmsg': 'do not contains user\'s info'
            }), 400

    # dragon info
    dragon_id = data['dragon_id']
    dragon = Dragon.query.get_or_404(data['dragon_id'])

    print(data)

    # member info
    mo = MemberOpenID.query.filter_by(openid=data['openid']).first_or_404()
    mo.nickname = data['nickname']
    mo.avatarUrl = data['avatarUrl']

    do = DragonOrder.query.filter_by(dragon_id=dragon_id, member_id=mo.id).first()
    if not do:
        code = datetime.now().strftime('%Y%m%d%H%M%S%f')
        do = DragonOrder(code)
        do.dragon_id = dragon_id
        do.dragon = dragon

        do.member_id = mo.id
        do.member = mo

        # products info
        do.original_price = Decimal(0)
        do.real_price = Decimal(0)
        do.products = []
        #pcs = [p['code'] for p in data['products']]
        for p in data['products']:
            dop = DragonOrderProduct()
            #dop.order = do
            dop.dragon_order_code = code
            product = Product.query.filter_by(code=p['code']).first_or_404()
            dp = DragonProduct.query.filter_by(dragon_id=dragon.id, product_id=product.id).first_or_404()
            dop.product = dp
            dop.amount = int(p['want_amount'])
            dp.sold += dop.amount
            do.original_price += product.original_price * dop.amount
            do.real_price += dp.price * dop.amount
            do.products.append(dop)
            print(do.products, data['products'])

        # delivery info
        if data['to_delivery']:
            # create a delivery address for user
            ma = DeliveryAddress()
            ma.name = data['delivery_name']
            ma.phone = data['delivery_phone']
            ma.address = data['delivery_address']
            do.delivery_address = ma
            do.real_price += dragon.delivery_fee if dragon.delivery_fee else 0
        else:
            da = DragonAddress.query.get_or_404(data['base_address'])
            do.address = da

        do.note = data['note']

        do.payment = data['payment']
        if  do.payment == 2: # value card pay
            do.member.name = data['member_name']
            do.member.phone = data['member_phone']
            do.pay_time = datetime.now()
            do.payment_code = do.code
            do.seq = _get_next_seq(dragon_id)


    if do.payment == 4 and (not do.prepay_id_expires or do.prepay_id_expires < int(time())):
        # invoke the unified order interface of WeChat
        result = unified_order(do, shop.weixin_mini_appid, shop.weixin_mchid, shop.weixin_pay_secret, data['openid'], url_for('api.pay_notify', shop=shop.code, _external=True), shop.code)
        if result['return_code'] == 'SUCCESS' and result['result_code'] == 'SUCCESS':
            do.prepay_id = result['prepay_id']
            do.prepay_id_expires = int(time()) + 7200 - 10 # prepay_id的过期时间是2小时
            do.seq = _get_next_seq(dragon_id)

    do.save()
    d = do.to_json()
    # to generate parameters for wx.requestPayment
    print('888888888888888888888888888888', do.payment)
    if do.payment == 4:
        dm = {
            'appId': shop.weixin_mini_appid,
            'timeStamp': str(int(time())),
            'nonceStr': uuid4().hex,
            'package': '='.join(['prepay_id', do.prepay_id]),
            'signType': 'MD5',
        }
        dm['paySign'], signType = generate_pay_sign(dm, shop.weixin_pay_secret)
        d.update(dm)
    else:
        notify_admins(do, shop.get_access_token(), data['formId'])

    d['access_token'] = shop.get_access_token()

    return jsonify(d), 201


def withdraw_dragon(shoppoint, arg):
    # member info
    mo = MemberOpenID.query.filter_by(openid=arg['openid']).first_or_404()

    # dragon info
    dragon = Dragon.query.get_or_404(arg['dragon_id'])

    # dragon order
    do = DragonOrder.query.filter_by(dragon_id=dragon.id, member_id=mo.id).first_or_404()

    order_type = ''
    if do.payment & 2: # 包含有会员支付
        order_type += ' 会员支付'
    if do.payment & 4:
        order_type += ' 微信支付'


    # 提醒接龙发起者，顾客取消了订单
    if do.address:
        data = {
            "keyword5":{
                "value": "自提" + order_type,
                },
            "keyword6":{
                "value": do.member.name if do.payment&2 else do.member.nickname,
                },
            "keyword7":{
                "value": do.member.phone if do.payment&2 else '',
                },
            "keyword8":{
                "value": do.address.address,
                },
            }
    else:
        data = {
            "keyword5":{
                "value": "送货" + order_type,
                },
            "keyword6":{
                "value": do.member.name if do.payment&2 else do.delivery_address.name,
                },
            "keyword7":{
                "value": do.member.phone if do.payment&2 else do.delivery_address.phone,
                },
            "keyword8":{
                "value": do.delivery_address.address,
                },
            }
    data.update({
        "keyword1": {
            "value": do.code,
            },
        "keyword2": {
            "value": do.payment_code,
            },
        "keyword3":{
            "value": ','.join(["x".join([p.product.product.name, str(p.amount)]) for p in do.products]),
            },
        "keyword4":{
            "value": '￥' + str(do.real_price),
            },
        "keyword9":{
            "value": '会员消费，联系人和联系电话就是会员的姓名与会员电话，请注意反结账或者退货',
            },
    })

    mos = MemberOpenID.query.filter_by(shoppoint_id=shoppoint.id, privilege=1).all()
    for mo in mos:
        j = {
            'template_id': 'dSAwUbWoHwYcKct2OZ7QU3mdhd6aGZtYaeG-6AbmGL4',
            'touser': mo.openid,
            #'url':  url_for('shop.payresult', _external=True, ticket_code=do.code),
            'form_id': arg['formId'],
            'data': data,
            "emphasis_keyword": "keyword4.DATA"
            }
        body = json.dumps(j)
        result = post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send', body, access_token=shoppoint.get_access_token())
        print(result)

    # delete the products of this dragon
    do.withdraw()

    return jsonify({
        'errcode': 201,
        'errmsg': 'withdraw ok'
        }), 201

@api.route('/<shop>/dragon/order/info', methods=['GET', 'POST'])
def dragon_order_info(shop):
    sp = Shoppoint.query.filter_by(code=shop).first_or_404()
    if request.method == 'POST': # new or modify dragon order
        # to check the member
        data = json.loads(request.data.decode('utf-8'))

        if data['operate'] == 'join':
            return join_dragon(sp, data)
        elif data['operate'] == 'withdraw':
            return withdraw_dragon(sp, data)
        else:
            return jsonify({
                'errcode': 400,
                'errmsg': 'bad request'
                }), 400
    elif requst.method == 'GET': # get dragon order info according to primary key
        return jsonify({}), 200

from ..weixin.message import parse_message

def post_weixin_api(url, body, **kwargs):
    params = urlencode(kwargs)
    final_url = '?'.join([url, params])
    data = body.encode('utf-8')
    with urlopen(final_url, data=data) as f:
        result = f.read().decode('utf-8')

        info = json.loads(result)

        return info

def notify_admins(do, access_token, formId=None):
    # 提醒接龙发起者有新订单了
    if do.address:
        data = {
            "keyword4":{
                "value": "自提",
                },
            "keyword5":{
                "value": do.address.address,
                },
            "keyword6":{
                "value": do.member.nickname + ' 拼团编号:' + str(do.seq),
                },
            "keyword7":{
                "value": '',
                },
            }
    else:
        data = {
            "keyword4":{
                "value": "送货",
                },
            "keyword5":{
                "value": do.delivery_address.address,
                },
            "keyword6":{
                "value": do.delivery_address.name + ' 拼团编号:' + str(do.seq),
                },
            "keyword7":{
                "value": do.delivery_address.phone,
                },
            }

    data.update({
        "keyword1": {
            "value": do.code,
            },
        "keyword2":{
            "value": ','.join(["x".join([p.product.product.name, str(p.amount)]) for p in do.products]),
            },
        "keyword3":{
            "value": '￥' + str(do.real_price),
            },
        "keyword8":{
            "value": do.note,
            },
        "keyword9":{
            "value": ("微信已支付" if do.pay_time and do.payment_code else "微信未支付") if do.payment == 4 else '请注意确认会员卡，会员: ' + do.member.name + '[' + do.member.phone + ']',
            }
    })

    mos = MemberOpenID.query.filter_by(privilege=1).all()
    for mo in mos:
        j = {
            'template_id': '2IFBivZUlocpzX-jM5etKReqveFPPn1NaHF--lwjH1A',
            'touser': mo.openid,
            #'url':  url_for('shop.payresult', _external=True, ticket_code=do.code),
            'form_id': formId if formId else do.prepay_id,
            'data': data,
            "emphasis_keyword": "keyword3.DATA"
            }
        body = json.dumps(j)
        print(body)
        result = post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send', body, access_token=access_token)
        print('8888888888888888888888 result', result)

@api.route('/<shop>/pay/notify', methods=['GET', 'POST'])
def pay_notify(shop):
    shoppoint = Shoppoint.query.filter_by(code=shop).first_or_404()
    message = parse_message(request.data.decode('utf-8'))
    if not message:
        abort(400)

    print(message)

    if message.get_value('result_code') != 'SUCCESS' or message.get_value('return_code') != 'SUCCESS':
        return "<xml><return_code><![CDATA[{0}]]></return_code><return_msg><![CDATA[{1}]]></return_msg></xml>".format(
                                                     message.get_value('result_code'), message.get_value('return_code'))

    if not message.check_signature(shoppoint.weixin_mini_appsecret):
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[签名不正确]]></return_msg></xml>"

    do = DragonOrder.query.get(message.get_value('out_trade_no'))
    if not do:
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[out trade no error]]></return_msg></xml>"

    do.payment_code = message.get_value('transaction_id')
    if int(do.real_price * 100) <= int(message.get_value('cash_fee')):
        do.pay_time = datetime.strptime(message.get_value('time_end'), '%Y%m%d%H%M%S')

    #db.session.add(do)
    db.session.commit()

    notify_admins(do, shoppoint.get_access_token())

    """
    # 提醒顾客订单已经付款
    data = {
        "keyword1": {
            "value": do.code,
            "color": "orange"
            },
        "keyword2":{
            "value": ','.join(["*".join([p.product.product.name, str(p.amount)]) for p in do.products]),
            "color":"#754c24"
            },
        "keyword3":{
            "value": '￥' + str(do.real_price),
            "color":"#754c24"
            },
        "keyword4":{
            "value": "自提" if do.address else "送货",
            "color":"#754c24"
            },
        "keyword5":{
            "value": '￥' + str(do.member.address),
            "color":"#754c24"
            },
        "keyword6":{
            "value": '￥' + str(do.member.nickname),
            "color":"#754c24"
            },
        "keyword7":{
            "value": '￥' + str(do.member.phone),
            "color":"#754c24"
            },
        "keyword8":{
            "value": do.note,
            "color":"#754c24"
            },
        "keyword9":{
            "value": "已支付" if do.pay_time and do.payment_code else "未支付",
            "color":"#754c24"
            }
    }
    j = {
        'template_id': 'x61QivvlgTGlNGuKDX8lYprf1EbgLw8Vv6MneCHSEmw',
        'touser': message.get_value('openid'),
        'url':  url_for('shop.payresult', _external=True, ticket_code=do.code),
        'form_id': do.prepay_id,
        'data': data
        }
    body = json.dumps(message.generate_template_body('hes3WdAVpnWrS1VenAUM8MFJbKQmTlKnBLOr7SAuvcI',
         message.get_value('openid'), url_for('shop.payresult', _external=True, ticket_code=do.code), data))
    post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/template/send', body, access_token=shoppoint.access_token)
    """

    return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"

    if result.get('return_code') == 'SUCCESS':
        do.payment_code = result.get('prepay_id')
        package = '='.join(['prepay_id', result.get('prepay_id')])
        params = {
            'timeStamp': int(time()),
            'appId': sp.weixin_mini_appid,
            'nonceStr': result.get('nonce_str'),
            'package': package,
            'signType': 'MD5'
        }
        params['signature'], signType = generate_pay_sign(params, sp.weixin_appsecret)
        params['pack'] = [package]

        do.save()

        return jsonify({
            'order': do.to_json(),
            'payment': params}), 201

    elif result.get('result_code') == 'FAIL' and result.get('err_code') == 'OUT_TRADE_NO_USED':
        return result, 409
