from flask import Flask
#from flask_mail import Mail
#from flask.ext.moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
#from flask_pagedown import PageDown
from config import config

from .filters import weixin_authorize

#bootstrap = Bootstrap()
#mail = Mail()
#moment = Moment()
db = SQLAlchemy()
#api = APIManager()
#pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    #bootstrap.init_app(app)
    #mail.init_app(app)
    #moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    #pagedown.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    app.jinja_env.filters['weixin_authorize'] = weixin_authorize

    from .product import product as product_blueprint
    app.register_blueprint(product_blueprint, url_prefix='/manage')

    #from .bakery import bakery as bakery_blueprint
    #app.register_blueprint(bakery_blueprint, url_prefix='/manage/bakery')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .sale import sale as sale_blueprint
    app.register_blueprint(sale_blueprint, url_prefix="/sale")

    from .gallery import gallery as gallery_blueprint
    app.register_blueprint(gallery_blueprint, url_prefix='/gallery')

    from .weixin import weixin as weixin_blueprint
    app.register_blueprint(weixin_blueprint, url_prefix='/weixin')

    from .shop import shop as shop_blueprint
    app.register_blueprint(shop_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
