from decimal import Decimal

from flask import render_template
from flask import request, current_app

from . import weixin

from ..models import Product, ProductCategory
from ..models import Parameter, ParameterCategory, ProductParameter

def check_signature(code, signature, timestamp, nonce):
    token = current_app.config['WEIXIN_TOKEN']
    #shoppoint = Shoppoint.query.filter_by(code=code).first()
    #token = shoppoint.weixin_token
    if signature and timestamp and nonce:
        array = [token, timestamp, nonce]
        array = array.sort()
        joined = "".join(array)

        joined_sha1 = hashlib.sha1(bytes(joined, 'ascii')).hexdigest()
        if joined_sha1 == signature:
            return True

        return False

@weixin.route('/access', methods=['GET'])
def access():
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    echostr = request.args.get('echostr')

    if check_signature('TODO', signature, timestamp, nonce):
        return echostr
    return "you're not weixin"

@weixin.route('/pay/', methods=['POST'])
def pay():
    return 'OK'
