import os
import urllib

from flask import json
from flask import current_app

from .. import db

from ..models import Shoppoint
from ..models import Member, Image

from ..exceptions import AccessTokenGotError

def _access_weixin_api(url, **kwargs):
    print ('accesssing ', url)
    params = urllib.parse.urlencode(kwargs).encode('utf-8')
    print (params)
    with urllib.request.urlopen(url, params) as f:
        result = f.read().decode('utf-8')
        print (result)
        info = json.loads(result)

        return info

def access_weixin_api(url, param_tuples):
    print ('accesssing ', url)
    params = urllib.parse.urlencode(param_tuples).encode('utf-8')
    print (params)
    with urllib.request.urlopen(url, params) as f:
        result = f.read().decode('utf-8')
        print (result)
        info = json.loads(result)

        return info

def store_weixin_picture(url, name):
    if not url or not name:
        return

    print(url)
    with urllib.request.urlopen(url) as f:
        p = open(os.path.join(current_app.config['UPLOAD_FOLDER'], '.'.join([name, 'jpg'])), 'wb')
        p.write(f.read())

        image = Image(name, name, current_app.config['UPLOAD_FOLDER'], 'jpg')
        db.session.add(image)
        db.session.commit()

def get_member_info(openid, language='zh-CN'):
    token = Shoppoint.query.first().weixin_access_token
    info = _access_weixin_api('https://api.weixin.qq.com/cgi-bin/user/info?%s', access_token=token, openid=openid, lang=language)
    if 'errcode' in info:
        errcode = info.get('errcode')
        errmsg = info.get('errmsg')

        return errcode, errmsg

    return info
    #subscribe = info.get('subscribe')
    #if subscribe:
    #    openid = info.get('openid')
    #    nickname = info.get('nickname')
    #    sex = info.get('sex')
    #    lang = info.get('language')
    #    city = info.get('city')
    #    province = info.get('province')
    #    country = info.get('country')
    #    headimgurl = info.get('headimgurl')
    #    subscribe_time = info.get('subscribe_time')
    #    unionid = info.get('unionid')
    #    remark = info.get('remark')
    #    groupid = info.get('groupid')
    #    tagid = sum(info.get('tagid_list'))

    #    #wm = WeixinMember(openid, unionid, subscribe, nickname, sex, city, country, province, headimgurl, remark, groupid, tagid, lang, subscribe_time)
    #    #db.session.add(wm)
    #    #db.session.commit()
    #else:
    #    openid = info.get('openid')
    #    unionid = info.get('unionid')
