import hashlib
from decimal import Decimal

from flask import render_template
from flask import request, current_app, make_response

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
        from flask import json
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

def generate_xml_response(to_username, from_username):
    from time import time
    string = '''<xml>
    <ToUserName><![CDATA[%s]]></ToUserName>
    <FromUserName><![CDATA[%s]]></FromUserName>
    <CreateTime>%d</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[Hello]]></Content>
    </xml>''' % (to_username, from_username, int(time()))

    response = make_response()
    response.headers['Content-type'] = 'application/xml'
    print(string)
    response.data = string.encode('utf-8')
    print (response)

    return response

def parse_xml(xmlstring):
    import xml.etree.ElementTree as etree
    tree = etree.fromstring(xmlstring)
    to_username = tree.find('ToUserName').text
    from_username = tree.find('FromUserName').text
    create_time = tree.find('CreateTime')
    msg_type = tree.find('MsgType')

    content = tree.find('Content')
    msg_id = tree.find('MsgId')

    return generate_xml_response(from_username, to_username)


    #event = tree.find('Event')

    #event_key = tree.find('EventKey')
    #ticket = tree.find('Ticket')

    #latitude = tree.find('Latitude')
    #longitude = tree.find('Longitude')
    #precision = tree.find('Precision')

    #print (to_username, from_username, create_time,
    #       msg_type, event, event_key, latitude, longitude, precision)
    #return to_username, from_username, create_time, msg_type,
    #       event, event_key, latitude, longitude, precision;

@weixin.route('/access', methods=['GET', 'POST'])
def access():
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    if request.method == 'GET':
        echostr = request.args.get('echostr')
        if check_signature('TODO', signature, timestamp, nonce):
            return echostr
        return "you're not weixin"
    else:
        openid = request.args.get('openid')
        result = parse_xml(request.data.decode('utf-8'))
        return result


@weixin.route('/pay/', methods=['POST'])
def pay():
    get_access_token()
    return 'OK'
