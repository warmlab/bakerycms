import urllib

from flask import json
from flask import current_app

from werkzeug.contrib.cache import MemcachedCache

from ..models import Member

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

def _get_access_token(force=False):
    cache = MemcachedCache(['/var/run/memcached/bakerycms.sock']) #TODO move memcached socket to config
    if not force:
        access_token = cache.get('WEIXIN_ACCESS_TOKEN')

        if access_token:
            print('access_token in memcached: ', access_token)
            return access_token

    print ('force to get token from weixin or cannot get access token from cache, get from weixin')
    app_id = current_app.config['WEIXIN_APPID']
    app_secret = current_app.config['WEIXIN_APPSECRET']

    # get access token
    #params = urllib.parse.urlencode({'grant_type': 'client_credential', 'appid': app_id, 'secret': app_secret})
    #params = params.encode('ascii')
    #with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", params) as f:
    #    result = f.read().decode('utf-8')
    #    print (result)
    #    j = json.loads(result)
    info = _access_weixin_api("https://api.weixin.qq.com/cgi-bin/token?%s",
                            grant_type='client_credential', appid=app_id, secret=app_secret)
    if 'errcode' in info or 'access_token' not in info or 'expires_in' not in info:
        errcode = info.get('errcode')
        errmsg = info.get('errmsg')
        raise AccessTokenGotError(errcode, errmsg)

    access_token = info.get('access_token')
    timeout = info.get('expires_in') - 5
    cache.set('WEIXIN_ACCESS_TOKEN', access_token, timeout=timeout)
    return access_token

def get_member_info(openid, language='zh-CN'):
    token = _get_access_token()
    info = _access_weixin_api('https://api.weixin.qq.com/cgi-bin/user/info?%s', access_token=token, openid=openid, lang=language)
    if 'errcode' in info:
        errcode = info.get('errcode')
        errmsg = info.get('errmsg')

        return errcode, errmsg

    subscribe = info.get('subscribe')
    if subscribe:
        openid = info.get('openid')
        nickname = info.get('nickname')
        sex = info.get('sex')
        lang = info.get('language')
        city = info.get('city')
        province = info.get('province')
        country = info.get('country')
        headimgurl = info.get('headimgurl')
        subscribe_time = info.get('subscribe_time')
        unionid = info.get('unionid')
        remark = info.get('remark')
        groupid = info.get('groupid')
        tagid = sum(info.get('tagid_list'))

        #wm = WeixinMember(openid, unionid, subscribe, nickname, sex, city, country, province, headimgurl, remark, groupid, tagid, lang, subscribe_time)
        #db.session.add(wm)
        #db.session.commit()
    else:
        openid = info.get('openid')
        unionid = info.get('unionid')
