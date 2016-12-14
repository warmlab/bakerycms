import hashlib
import urllib
from uuid import uuid4
from time import time

from flask import json

from xml.etree import ElementTree as etree


def generate_sign(params, key=None):
    """
    签名生成函数
       
    :param params: 参数，dict 对象
    :param key: API 密钥
    :return: sign string
    """
    param_list = []
    for k,v in params.items():
        if v:
            param_list.append('='.join([k, str(v)]))

    param_list.sort()
    if key:
        param_list.append('='.join(['key', key]))
    print(param_list)

    print('&'.join(param_list))
    return hashlib.md5('&'.join(param_list).encode('utf8')).hexdigest().upper(), 'MD5' # TODO 考虑HMAC-SHA256

def convert_to_xml_cdata(data):
    return data.join(['<![CDATA[',']]>'])

def parse_xml_to_dict(xmlbody):
    root = etree.fromstring(xmlbody)

    data = {}
    for e in root:
        data[e.tag] = e.text

    return data

def parse_dict_to_xml(dic):
    items = []
    for k,v in dic.items():
        if k == 'total_fee' or k == 'mch_id':
            items.append('<{key}>{value}</{key}>'.format(key=k, value=v))
        else:
            items.append('<{key}>{value}</{key}>'.format(key=k, value=convert_to_xml_cdata(v)))

    return ''.join(items).join(['<xml>','</xml>'])

def _make_goods_info(ticket_products):
    goods_list = []
    for tp in ticket_products:
        goods = {}
        goods['goods_id'] = tp.product.code
        goods['wxpay_goods_id'] = tp.product.code
        goods['goods_name'] = tp.product.name
        goods['quantity'] = tp.amount
        goods['price'] = int(tp.real_price * 100)
        goods['goods_category'] = tp.product.category.name
        goods['body'] = '卡诺烘焙-只用100%天然乳脂奶油'

        goods_list.append(goods)

    goods_detail = {'goods_detail': goods_list}

    return json.dumps(goods_detail)

# 统一下单，WxPayUnifiedOrder中out_trade_no、body、total_fee、trade_type必填
# appid、mchid、spbill_create_ip、nonce_str不需要填入
# @return 成功时返回，其他抛异常
def unified_order(ticket, appid, mch_id, key, user, notify_url, device_info='WEB', trade_type='JSAPI', time_out=6):
    url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    data = {}

    if not ticket or not appid or not mch_id or not key:
        return

    data['out_trade_no'] = ticket.code
    data['body'] = '卡诺烘焙-只用100%天然乳脂奶油' # 商品简单描述
    data['total_fee'] = int(ticket.real_price * 100) # 转换成分
    data['trade_type'] = trade_type
    data['openid'] = user.member.weixin_openid
    data['device_info'] = device_info

    # 异步通知url未设置，则使用配置文件中的url
    data['notify_url'] = notify_url

    data['appid'] = appid #公众账号ID
    data['mch_id'] = mch_id #商户号
    data['nonce_str'] = uuid4().hex #随机字符串
    data['spbill_create_ip'] = '121.42.139.198'
    #data['attach'] = '卡诺烘焙-微信小店'
    #data['detail'] = _make_goods_info(ticket.products)

    # 签名
    data['sign'], sign_type = generate_sign(data, key)
    xml = parse_dict_to_xml(data)

    #startTimeStamp = int(time())
    req = urllib.request.Request(url=url,
            data=xml.encode('utf-8'), method='POST')
    req.add_header('Accept', 'application/xml')
    req.add_header('Content-Type', 'application/xml')
    with urllib.request.urlopen(req) as f:
        result = f.read().decode('utf8')

        return parse_xml_to_dict(result)
    #self.reportCostTime($url, $startTimeStamp, $result); #上报请求花费时间

def unified_order_js_config(appid, key):
    params = {'timeStamp': int(time()),
              'nonceStr': uuid4().hex,
              'appId': appid,
             }

    params['signature'], sign_type = generate_sign(params, key)

    return params
