import urllib

from datetime import datetime

from flask import json
from flask import request
from flask.json import jsonify

from . import api

from ..models import Dragon, DragonAddress
from ..models import Product, Shoppoint

@api.route('/<shop>/dragon/auth', methods=['GET'])
def dragon_auth(shop):
    #j = json.loads(request.data.decode('utf-8'))
    code = request.args['code']

    sp = Shoppoint.query.filter_by(code=shop).first()
    if not sp:
        abort(404)

    data = {
        'grant_type': 'authorization_code',
        'appid': sp.weixin_mini_appid,
        'secret': sp.weixin_mini_appsecret,
        'js_code': code
    }
    print(data)

    param = urllib.parse.urlencode(data).encode('utf-8')
    with urllib.request.urlopen('https://api.weixin.qq.com/sns/jscode2session', param) as s:
        result = s.read().decode('utf-8')
        print(result)
        info = json.loads(result)


        return jsonify(info)

    abort(403)

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
    if d["is_default"]:
        DragonAddress.query.update({"is_default":False})
    address.save()
    
    return jsonify(address.to_json()), 201


@api.route('/<shop>/dragon/new', methods=['PUT'])
def dragon_new(shop):
    #sp = Shoppoint.query.filter_by(name=shop).first()
    #if not sp:
    #    abort(404)

    data = json.loads(request.data.decode('utf-8'))
    print(data)

    #products = Product.query.filter(Product.code.in_([p.code for p in data['products'])).all()
    addresses = DragonAddress.query.filter(DragonAddress.id.in_(data['addrs_sel'])).all()

    dragon = Dragon('dragon', data['products'], data['products_bind'], data['is_member_card'], addresses, data['from_date'], data['from_time'], data['to_date'], data['to_time'], data['publish'], data['publish_date'], data['publish_time'])
    dragon.delivery_fee = data['delivery_fee']

    dragon.save()

    return jsonify(dragon.to_json()), 201


@api.route('/<shop>/dragon/latest', methods=['GET'])
def dragon_latest(shop):
    today = datetime.now()
    dragon = Dragon.query.filter(Dragon.publish_time<=today).order_by(Dragon.publish_time.desc()).first()

    return jsonify(dragon.to_json())

@api.route('/<shop>/dragon/info/<code>', methods=['GET'])
def dragon_info(shop, code):
    #today = datetime.now()
    dragon = Dragon.query.get_or_404(code)

    return jsonify(dragon.to_json())

@api.route('/<shop>/dragon/orders', methods=['GET'])
def dragon_orders(shop):
    d = [
            {"nickname": '飞翔的猪1', "headimg": "", "amount": 1, "name": "张三", "address": "青岛市九水路227号宝龙城市广场3层小麦芬", "mobile": '12345678901', "timestamp":"2018/12/12 13:13:14"},
            {"nickname": '飞翔的猪2', "headimg": "", "amount": 2, "name": "张三", "address": "青岛市九水路227号宝龙城市广场3层小麦芬", "mobile": '12345678901', "timestamp":"2018/12/12 13:13:14"},
            {"nickname": '飞翔的猪3', "headimg": "", "amount": 2, "name": "张三", "address": "青岛市九水路227号宝龙城市广场3层小麦芬", "mobile": '12345678901', "timestamp":"2018/12/12 13:13:14"},
            {"nickname": '飞翔的猪4', "headimg": "", "amount": 2, "name": "张三", "address": "青岛市九水路227号宝龙城市广场3层小麦芬", "mobile": '12345678901', "timestamp":"2018/12/12 13:13:14"}
    ]

    return  jsonify(d)

@api.route('/<shop>/dragon/order/info', methods=['GET', 'PUT'])
def dragon_order_info(shop):
    if request.method == 'PUT': # new or modify dragon order
        # to check the member
        data = json.loads(request.data.decode('utf-8'))
        print(data)

        return jsonify({'a': 'b'}), 201
    elif requst.method == 'GET': # get dragon order info according to primary key
        return jsonify({'a': 'b'}), 200
