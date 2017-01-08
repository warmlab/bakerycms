import hashlib
from decimal import Decimal
from datetime import datetime

from flask import render_template, abort
from flask import request, current_app, make_response
from flask import json

from flask_login import login_required, current_user

from . import weixin
from .. import db
from .message import parse_message, Message
from .access import get_member_info, store_weixin_picture, post_weixin_api

from ..models import Shoppoint, Member, Ticket
from ..models import Parameter, ParameterCategory, ProductParameter

from ..decorators import member_required

def check_signature(code, signature, timestamp, nonce):
    #token = current_app.config['WEIXIN_TOKEN']
    shoppoint = Shoppoint.query.first()
    token = shoppoint.weixin_token
    if signature and timestamp and nonce:
        array = [token, timestamp, nonce]
        array.sort()
        joined = "".join(array)

        joined_sha1 = hashlib.sha1(bytes(joined, 'ascii')).hexdigest()
        if joined_sha1 == signature:
            return True

        return False

@weixin.route('/access', methods=['GET', 'POST'])
def access():
    shoppoint = Shoppoint.query.first()
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    if request.method == 'POST':
        openid = request.args.get('openid')
        body = request.data.decode('utf-8')
        message = parse_message(body)
        if message.type == 'event':
            if message.event == 'subscribe':
                info = get_member_info(openid)
                if 'openid' in info:
                    member = Member.query.filter_by(weixin_openid=info.get('openid'))
                    if member:
                        member.weixin_unionid = info.get('unionid')
                        member.gender = info.get('sex')
                        member.nickname = info.get('nickname')
                        message.member = member
                body = message.generate_response_body()
                response = make_response()
                response.headers['Content-type'] = 'application/xml'
                response.data = body.encode('utf-8')

                return response
            elif message.event == 'user_pay_from_pay_cell':
                data = {
                    "productType": {
                        "value":"卡诺烘焙",
                        },
                    "name":{
                        "value":"用心做，不做作",
                        "color":"#754c24"
                        },
                    'accountType':{"value":"金额"},
                    'account':{
                        "value": '￥' + str(int(message.get_value('Fee')) / 100),
                        "color":"#754c24"
                        },
                    "time": {
                        "value": datetime.fromtimestamp(int(message.get_value('CreateTime'))).strftime('%X'),
                        "color":"#754c24"
                        },
                    "remark":{
                        "value":"只用天然乳脂奶油。只用优质供应商的高品质原料",
                        "color":"#754c24"
                        }
                }
                body = json.dumps(message.generate_template_body('9EMNExtVNw81PxQt7dT0mTeWhJjDOvmo_dn48Y_tdLE',
                                                                 message.get_value('FromUserName'), data))
                post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/template/send', body, access_token=shoppoint.access_token)

                return ""
            elif message.event == 'submit_membercard_user_info':
                #if not openid:
                #    openid = message.get_value('FromUserName')
                #info = get_member_info(openid)
                #print (info)
                data = {
                    "first": {
                        "value":"感谢您成为卡诺烘焙会员",
                        },
                    "cardNumber":{
                        "value": message.get_value('UserCardCode'),
                        "color":"#754c24"
                        },
                    'type':{"value":"卡诺"},
                    'address': {
                        "value": shoppoint.address,
                        "color":"#754c24"
                        },
                    #'VIPName': {
                    #    "value": '您好',
                    #    "color":"#754c24"
                    #    },
                    #'VIPPhone': {
                    #    "value": '12345678901',
                    #    "color":"#754c24"
                    #    },
                    "remark":{
                        "value":"只用天然乳脂奶油。只用优质供应商的高品质原料",
                        "color":"#754c24"
                        }
                }
                body = json.dumps(message.generate_template_body('YXKo5tUIvkDpd_x9T6HgI3twkIGMLrcDoVIBWNPOkUA',
                                                                  message.get_value('FromUserName'), data))
                post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/template/send', body, access_token=shoppoint.access_token)

                return ""
            elif message.event == 'CLICK':
                if message.event_key == 'my_phone':
                    body = message.generate_response_body()
                    response = make_response()
                    response.headers['Content-type'] = 'application/xml'
                    response.data = body.encode('utf-8')

                    return response
                elif message.event_key == 'my_location':
                    body = message.generate_location_body()
                    response = make_response()
                    response.headers['Content-type'] = 'application/xml'
                    response.data = body.encode('utf-8')

                    return response
            else:
                return ""
        elif message.type == 'image':
            if message.get_value('FromUserName') in ('ox4bxso53hocK9iyC-eKNll-qRoI',
                    'ox4bxsnBj7xpsSndE4TOg_LY-IKQ', 'ox4bxsn8gkt_IqaVzQIPRkuep4v8'): # TODO
                # save image to gallery
                store_weixin_picture(message.get_value('PicUrl'), message.get_value('MsgId'))
        else:
            body = message.generate_response_body()
            response = make_response()
            response.headers['Content-type'] = 'application/xml'
            response.data = body.encode('utf-8')

            return response
    else:
        echostr = request.args.get('echostr')
        if check_signature('TODO', signature, timestamp, nonce):
            return echostr
        abort(400)

@weixin.route('/pay/', methods=['POST'])
@login_required
@member_required
def pay():
    return 'OK'

@weixin.route('/pay/test/', methods=['POST'])
@login_required
@member_required
def pay_test():
    return 'OK'

@weixin.route('/pay/callback', methods=['POST'])
@login_required
@member_required
def pay_callback():
    print ('in weixin pay callback')
    print(request.method)
    print(request.args)
    return 'OK'

@weixin.route('/pay/notify', methods=['GET', 'POST'])
def pay_notify():
    shoppoint = Shoppoint.query.first()
    message = parse_message(request.data.decode('utf-8'))
    if not message:
        abort(400)

    if message.get_value('result_code') != 'SUCCESS' or message.get_value('return_code') != 'SUCCESS':
        return "<xml><return_code><![CDATA[{0}]]></return_code><return_msg><![CDATA[{1}]]></return_msg></xml>".format(
                                                     message.get_value('result_code'), message.get_value('return_code'))

    if not message.check_signature(shoppoint.weixin_appsecret):
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[签名不正确]]></return_msg></xml>"

    ticket = Ticket.query.get(message.get_value('out_trade_no'))
    if not ticket:
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[out trade no error]]></return_msg></xml>"

    ticket.payment_code = message.get_value('transaction_id')
    if int(ticket.real_price * 100) <= int(message.get_value('cash_fee')):
        ticket.pay_time = datetime.strptime(message.get_value('time_end'), '%Y%m%d%H%M%S')

    #db.session.add(ticket)
    db.session.commit()

    # 提醒经营者顾客付款订单了
    data = {
        "first": {
            "value":"新订单提醒: 单号: " + ticket.code,
            "color":"orange"
            },
        "keyword1":{
            "value": ','.join(["*".join([p.product.name, str(p.amount)]) for p in ticket.products]),
            "color":"#754c24"
            },
        "keyword2":{
            "value": '￥' + str(ticket.real_price),
            "color":"#754c24"
            },
        'keyword3':{
            "value": " ".join([ticket.address.contact_name, ticket.address.mobile, ticket.address.address, "配送时间: ", str(ticket.required_datetime)]),
            "color":"#754c24"
            },
        "keyword4": {
            "value": "在线支付: " + ticket.payment_code,
            "color":"#754c24"
            },
        "remark":{
            "value": ticket.note,
            "color":"#754c24"
            }
    }

    for u in ('ox4bxso53hocK9iyC-eKNll-qRoI',
            'ox4bxsnBj7xpsSndE4TOg_LY-IKQ', 'ox4bxsn8gkt_IqaVzQIPRkuep4v8'):
        body = json.dumps(message.generate_template_body('pkl-0GTnDHxthXtR381PPNAooBT1JwUYuuP-YK1nRSA',
                                                     u,  data))
        post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/template/send', body, access_token=shoppoint.access_token)

    # 提醒顾客订单已经付款
    data = {
        "first": {
            "value":"尊敬的顾客，您的订单已经完成支付-" + ticket.code,
            "color":"orange"
            },
        "keyword1":{
            "value": '￥' + str(ticket.real_price),
            "color":"#754c24"
            },
        "keyword2":{
            "value": ','.join(["*".join([p.product.name, str(p.amount)]) for p in ticket.products]),
            "color":"#754c24"
            },
        "remark":{
            "value": ticket.note,
            "color":"#754c24"
            }
    }
    body = json.dumps(message.generate_template_body('hes3WdAVpnWrS1VenAUM8MFJbKQmTlKnBLOr7SAuvcI',
                                                 message.get_value('openid'), data))
    post_weixin_api('https://api.weixin.qq.com/cgi-bin/message/template/send', body, access_token=shoppoint.access_token)

    return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"
