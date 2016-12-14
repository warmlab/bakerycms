import hashlib
from decimal import Decimal

from flask import render_template, abort
from flask import request, current_app, make_response

from flask_login import login_required, current_user

from . import weixin
from .message import parse_message, Message
from .access import get_member_info, store_weixin_picture

from ..models import Member
from ..models import Parameter, ParameterCategory, ProductParameter

from ..decorators import member_required

def check_signature(code, signature, timestamp, nonce):
    token = current_app.config['WEIXIN_TOKEN']
    #shoppoint = Shoppoint.query.filter_by(code=code).first()
    #token = shoppoint.weixin_token
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
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    if request.method == 'POST':
        openid = request.args.get('openid')
        body = request.data.decode('utf-8')
        message = parse_message(body)
        if message.type == 'event' and message.event == 'subscribe':
            info = get_member_info(openid)
            member = Member.query.filter_by(weixin_openid=info.get('openid'))
            if member:
                member.weixin_unionid = info.get('unionid')
                member.gender = info.get('sex')
                member.nickname = info.get('nickname')
                message.member = member
        elif message.type == 'image':
            if message.get_value('FromUserName') in ('ox4bxso53hocK9iyC-eKNll-qRoI',
                    'ox4bxsnBj7xpsSndE4TOg_LY-IKQ', 'ox4bxsn8gkt_IqaVzQIPRkuep4v8'): # TODO
                # save image to gallery
                store_weixin_picture(message.get_value('PicUrl'), message.get_value('MsgId'))
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
    return 'OK'

@weixin.route('/pay/notify', methods=['GET', 'POST'])
def pay_notify():
    return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'
