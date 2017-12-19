from urllib import parse as urlparse
#from jinja2 import evalcontextfilter, escape
#from jinja2 import Environment#, FileSystemLoader
import app
#environment = Environment()
#@evalcontextfilter
def weixin_authorize(redirect_url, scope): 
    conn = app.db.engine.connect()
    appid, expires_time = conn.execute('select weixin_appid, weixin_expires_time from shoppoint').first()
    conn.close()
    params = [('appid', appid), # get appid from db
              #('redirect_uri', url_for('.cart', _external=True)),
              ('redirect_uri', redirect_url),
              ('response_type', 'code'),
              #('scope', 'snsapi_userinfo')
              ('scope', scope)
            ]
    url = 'https://open.weixin.qq.com/connect/oauth2/authorize'
    url = '?'.join([url, urlparse.urlencode(params)])
    url = '#'.join([url, 'wechat_redirect'])
    return url
