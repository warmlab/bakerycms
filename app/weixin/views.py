import hashlib
from decimal import Decimal

from flask import render_template, abort
from flask import request, current_app, make_response

from flask_login import login_required, current_user

from . import weixin
from .message import parse_message, Message
from .access import get_member_info

from ..models import Product, ProductCategory
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
    if request.method == 'GET':
        echostr = request.args.get('echostr')
        if check_signature('TODO', signature, timestamp, nonce):
            return echostr
        abort(400)
    else:
        openid = request.args.get('openid')
        body = request.data.decode('utf-8')
        message = parse_message(body)
        if message.type == 'event' and message.event == 'subscribe':
            get_member_info(openid)
        body = message.generate_response_body()
        response = make_response()
        response.headers['Content-type'] = 'application/xml'
        response.data = body.encode('utf-8')

        return response

@weixin.route('/pay/', methods=['POST'])
@login_required
@member_required
def pay():
    return 'OK'
