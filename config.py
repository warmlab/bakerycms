import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    CARO_MAIL_SUBJECT_PREFIX = '[CAROBakery]'
    CARO_MAIL_SENDER = 'CAROBakery Admin <bzip@qq.com>'
    CARO_ADMIN = os.environ.get('CAROBAKERY_ADMIN')
    CARO_POSTS_PER_PAGE = 20
    CARO_FOLLOWERS_PER_PAGE = 50
    CARO_COMMENTS_PER_PAGE = 30
    CARO_SLOW_DB_QUERY_TIME=0.5
    UPLOAD_FOLDER = os.environ.get('BAKERYCMS_UPLOAD_DIR') or os.path.join(basedir, 'media')

    WEIXIN_TOKEN = 'c8316ff603da422fb790142141543ce2'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DB_USER = os.environ.get('DB_USER') or 'nouser'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'nopassword'
    DEBUG = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI =  'postgresql+psycopg2://%s:%s@127.0.0.1:5432/bakerycms' % (DB_USER, DB_PASSWORD)


class TestingConfig(Config):
    DB_USER = os.environ.get('DB_USER') or 'nouser'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'nopassword'
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_DATABASE_URI =  'postgresql+psycopg2://%s:%s@127.0.0.1:5432/bakerycms' % (DB_USER, DB_PASSWORD)
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DB_USER = os.environ.get('DB_USER') or 'nouser'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'nopassword'
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SQLALCHEMY_DATABASE_URI =  'postgresql+psycopg2://%s:%s@127.0.0.1:5432/bakerycms' % (DB_USER, DB_PASSWORD)

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.CARO_MAIL_SENDER,
            toaddrs=[cls.CARO_ADMIN],
            subject=cls.CARO_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig,
    'default': DevelopmentConfig
}
