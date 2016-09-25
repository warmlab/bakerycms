import hashlib
from decimal import Decimal

from flask import render_template
from flask import request, current_app

from werkzeug.contrib.cache import MemcachedCache

from . import weixin

from ..models import Product, ProductCategory
from ..models import Parameter, ParameterCategory, ProductParameter

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

def get_access_token():
    cache = MemcachedCache(['/var/run/memcached/bakerycms.sock']) #TODO move memcached socket to config
    access_token = cache.get('WEIXIN_ACCESS_TOKEN')
    if not access_token:
        print ('cannot get access token from cache, get from weixin')
        app_id = current_app.config['WEIXIN_APPID']
        app_secret = current_app.config['WEIXIN_APPSECRET']

        # TODO get access token
        import urllib
        import json
        params = urllib.parse.urlencode({'grant_type': 'client_credential', 'appid': app_id, 'secret': app_secret})
        params = params.encode('ascii')
        with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", params) as f:
            result = f.read().decode('utf-8')
            print (result)
            j = json.loads(result)
            access_token = j.get('access_token')
            timeout = j.get('expires_in') - 5
            print (access_token, timeout)
            cache.set('WEIXIN_ACCESS_TOKEN', access_token, timeout=timeout)
    else:
        print('access_token in memcached: ', access_token)
    return access_token

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
    get_access_token()
    return 'OK'
