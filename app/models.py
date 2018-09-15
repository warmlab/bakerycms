from datetime import datetime
from time import time
#import hashlib
import urllib

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
#from markdown import markdown
#import bleach
from flask import current_app#, url_for
from flask import json, jsonify

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import or_
from sqlalchemy.types import Enum
from .exceptions import AccessTokenGotError
from .extensions import login_manager
from flask_login import UserMixin, AnonymousUserMixin

db = SQLAlchemy()

class Shoppoint(db.Model):
    __tablename__ = 'shoppoint'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, index=True)
    english_name = db.Column(db.String(64))
    name = db.Column(db.String(128))
    contact = db.Column(db.String(128)) # 店长或者负责人
    phone = db.Column(db.String(16)) # 店内固定电话
    mobile = db.Column(db.String(16))
    address = db.Column(db.String(1024))
    banner = db.Column(db.String(256)) # 广告语
    description = db.Column(db.Text)

    # mail section
    mail = db.Column(db.String(64))
    mail_server = db.Column(db.String(128))
    mail_port = db.Column(db.SmallInteger, default=587)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_login_name = db.Column(db.String(64))
    mail_login_password = db.Column(db.String(128))
    mail_subject_prefix = db.Column(db.String(64))
    mail_sender = db.Column(db.String(64))

    # 微信中的配置
    weixin_appid = db.Column(db.String(32))
    weixin_appsecret = db.Column(db.String(64))
    weixin_mchid = db.Column(db.String(16))
    weixin_token = db.Column(db.String(64)) # 服务器配置中的token
    weixin_aeskey = db.Column(db.String(128)) # 服务器配置中的EncodingAESKey
    weixin_access_token = db.Column(db.String(256))
    weixin_expires_time = db.Column(db.BigInteger) # timestamp
    weixin_jsapi_ticket = db.Column(db.String(256))
    weixin_jsapi_expires_time = db.Column(db.BigInteger) # timestamp
    weixin_mini_appid = db.Column(db.String(32))
    weixin_mini_appsecret = db.Column(db.String(64))
    weixin_pay_secret = db.Column(db.String(64))
    weixin_mini_access_token = db.Column(db.String(256))
    weixin_mini_expires_time = db.Column(db.BigInteger) # timestamp

    def __repr__(self):
        return self.name

    @property
    def access_token(self, provider='weixin'):
        if self.weixin_access_token and self.weixin_expires_time and self.weixin_expires_time > int(time()):
            return self.weixin_access_token

        print ('Get token from weixin or cannot get access token')

        # get access token
        #params = urllib.parse.urlencode({'grant_type': 'client_credential', 'appid': app_id, 'secret': app_secret})
        #params = params.encode('ascii')
        #with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", params) as f:
        #    result = f.read().decode('utf-8')
        #    print (result)
        #    j = json.loads(result)
        #info = _access_weixin_api("https://api.weixin.qq.com/cgi-bin/token?%s",
        #                        grant_type='client_credential', appid=self.weixin_appid, secret=self.weixin_appsecret)
        params = {'grant_type':'client_credential', 'appid':self.weixin_appid, 'secret':self.weixin_appsecret}
        url_param = urllib.parse.urlencode(params).encode('utf-8')
        with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", url_param) as f:
            result = f.read().decode('utf-8')
            print (result)
            info = json.loads(result)

            if 'errcode' in info or 'access_token' not in info or 'expires_in' not in info:
                errcode = info.get('errcode')
                errmsg = info.get('errmsg')
                raise AccessTokenGotError(errcode, errmsg)

            self.weixin_access_token = info.get('access_token')
            self.weixin_expires_time = int(time()) + info.get('expires_in') - 30
            db.session.commit()

            return self.weixin_access_token

    def get_access_token(self, provider='weixin'):
        if self.weixin_mini_access_token and self.weixin_mini_expires_time and self.weixin_mini_expires_time > int(time()):
            return self.weixin_mini_access_token

        print ('Get token from weixin or cannot get access token')

        # get access token
        #params = urllib.parse.urlencode({'grant_type': 'client_credential', 'appid': app_id, 'secret': app_secret})
        #params = params.encode('ascii')
        #with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", params) as f:
        #    result = f.read().decode('utf-8')
        #    print (result)
        #    j = json.loads(result)
        #info = _access_weixin_api("https://api.weixin.qq.com/cgi-bin/token?%s",
        #                        grant_type='client_credential', appid=self.weixin_appid, secret=self.weixin_appsecret)
        params = {'grant_type':'client_credential', 'appid':self.weixin_mini_appid, 'secret':self.weixin_mini_appsecret}
        url_param = urllib.parse.urlencode(params).encode('utf-8')
        with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/token?%s", url_param) as f:
            result = f.read().decode('utf-8')
            print (result)
            info = json.loads(result)

            if 'errcode' in info or 'access_token' not in info or 'expires_in' not in info:
                errcode = info.get('errcode')
                errmsg = info.get('errmsg')
                raise AccessTokenGotError(errcode, errmsg)

            self.weixin_mini_access_token = info.get('access_token')
            self.weixin_mini_expires_time = int(time()) + info.get('expires_in') - 30
            db.session.commit()

            return self.weixin_mini_access_token
        return ''

    @property
    def jsapi_ticket(self, provider='weixin'):
        if self.weixin_jsapi_ticket and self.weixin_jsapi_expires_time \
           and self.weixin_jsapi_expires_time > int(time()):
            return self.weixin_jsapi_ticket

        print ('Get token from weixin jsapi ticket or cannot get jsapi ticket')

        params = {'access_token': self.access_token, 'type': 'jsapi'}
        url_param = urllib.parse.urlencode(params).encode('utf-8')
        with urllib.request.urlopen("https://api.weixin.qq.com/cgi-bin/ticket/getticket?%s", url_param) as f:
            result = f.read().decode('utf-8')
            print (result)
            info = json.loads(result)

            if 'ticket' not in info or 'expires_in' not in info:
                errcode = info.get('errcode')
                errmsg = info.get('errmsg')
                raise AccessTokenGotError(errcode, errmsg)

            self.weixin_jsapi_ticket = info.get('ticket')
            self.weixin_jsapi_expires_time = int(time()) + info.get('expires_in') - 30
            db.session.commit()

            return self.weixin_jsapi_ticket

#class ThirdPartyConfigCategory(db.Model):
#    __tablename__ = 'third_party_config_category'
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String(64))
#    prefix = db.Column(db.String(64))
#
#class ThirdPartyConfig(db.Model):
#    __tablename__ = 'third_party_config'
#    id = db.Column(db.Integer, primary_key=True)
#    category = db.Column()
#    #prefix = db.Column(db.String(64))
#    suffix = db.Column(db.String(64))
#    value = db.Column(db.String(256))


class Address(db.Model):
    __tablename__ = 'address'
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(64))
    province = db.Column(db.String(64))
    city = db.Column(db.String(64))
    address = db.Column(db.String(256))
    zip_code = db.Column(db.String(8))
    contact_name = db.Column(db.String(128)) # 联系人或者收货人姓名/紧急联系人姓名
    mobile = db.Column(db.String(16))
    is_default = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('userauth.id'), nullable=True)
    user = db.relationship('UserAuth',
                         backref=db.backref('addresses', lazy="dynamic"))


class MemberGrade(db.Model): # 会员等级或分类
    __tablename__ = 'member_grade'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    discount = db.Column(db.Integer, default=100) # 100表示不打折, 80表示8折
    to_point = db.Column(db.Boolean, default=True) # 该类会员是否参与积分
    description = db.Column(db.Text)

    def __repr__(self):
        return self.name


class Member(db.Model):
    __tablename__ = 'member'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, index=True, nullable=True) # 实体会员卡的卡面卡号，没有实体卡，可以使用用户名
    name = db.Column(db.String(128), index=True) # 会员姓名
    gender = db.Column(db.SmallInteger, default=0) # 会员性别, 0为unkown
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    email = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(128)) # 会员姓名
    to_point = db.Column(db.Boolean, default=True) # 该会员是否参与积分
    points = db.Column(db.Integer, default=0) # 积分
    member_since = db.Column(db.DateTime, default=datetime.now)
    member_end = db.Column(db.DateTime, default=None)
    headimgurl = db.Column(db.String(1024)) # 头像
    about_me = db.Column(db.Text)

    grade_id = db.Column(db.Integer, db.ForeignKey('member_grade.id'))
    grade = db.relationship('MemberGrade',
                         backref=db.backref('members', lazy='dynamic'))

    weixin_openid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin
    weixin_unionid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin
    weixin_token = db.Column(db.String(256))
    weixin_refresh_token = db.Column(db.String(256))
    weixin_expires_time = db.Column(db.BigInteger)
    weixin_privilege = db.Column(db.String(128))

class MemberOpenID(db.Model):
    __tablename__ = 'member_openid'
    id = db.Column(db.Integer, primary_key=True)
    unionid = db.Column(db.String(64), unique=True) # used in weixin
    openid = db.Column(db.String(64), unique=True) # used in weixin
    nickname = db.Column(db.String(128)) # used in weixin
    avatarUrl = db.Column(db.String(2048))
    expires_time = db.Column(db.BigInteger)
    session_key = db.Column(db.String(64), unique=True) # used in weixin
    #generate_session_key = db.Column(db.String(128), unique=True) # used in weixin
    privilege = db.Column(db.Integer, default=0) # every bit as a privilege

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    member = db.relationship('Member', backref=db.backref('openids', lazy='dynamic'))

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('member_openid', lazy="dynamic"))

    # used in 实体卡卡号
    code = db.Column(db.String(64), index=True) # 实体会员卡的卡面卡号，没有实体卡，可以使用用户名
    phone = db.Column(db.String(16), index=True) #手机号码
    #email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(128)) # 会员姓名
    address = db.Column(db.String(512)) # 会员备注地址

    orders = db.relationship('DragonOrder', back_populates='member')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_json(self):
        d = {
                'openid': self.openid,
                #'session_key': self.generate_session_key,
                'dragon_create': True if int(self.privilege) & 1 else False, # TODO create an function to check the privilege
                'nickname': self.nickname,
                'avatarUrl': self.avatarUrl,
                'phone': self.phone,
                'name': self.name
            }

        if self.unionid:
            d['unionid'] = self.unionid

        return d

    def __repr__(self):
        return self.openid

class DeliveryAddress(db.Model):
    __tablename__ = 'delivery_address'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    phone = db.Column(db.String(16))
    address = db.Column(db.String(512))

    orders = db.relationship('DragonOrder', back_populates='delivery_address')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_json(self):
        d = {
                'name': self.name,
                'phone': self.phone,
                'address': self.address
                }

        return d

    def __repr__(self):
        return self.address

class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    identify_card_no = db.Column(db.String(64), unique=True, index=True) # 员工身份证
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(128))
    nickname = db.Column(db.String(64)) # 员工昵称
    login_name = db.Column(db.String(64), unique=True, index=True) # 登录名称
    pos_code = db.Column(db.String(4), unique=True, index=True) # POS登录名称
    about_me = db.Column(db.Text)
    staff_since = db.Column(db.DateTime, default=datetime.now)
    staff_end = db.Column(db.DateTime, default=None)

    def can(self, permission):
        return True # TODO

class UserAuth(db.Model, UserMixin):
    __tablename__ = 'userauth'
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    email = db.Column(db.String(64), unique=True, index=True)
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    openid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin
    password_hash = db.Column(db.String(128), nullable=False)
    #reset_password_token = db.Column(db.String(128), nullable=False)
    confirmed_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=False)
    #authenticated = db.Column(db.Boolean, default=False)

    # Relationships
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'))
    staff = db.relationship('Staff', uselist=False, foreign_keys=staff_id)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id', ondelete='CASCADE'))
    member = db.relationship('Member', uselist=False, foreign_keys=member_id)

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('userauth', lazy="dynamic"))

    bakery_classes = db.relationship('Bakery', back_populates="member")

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def confirmed(self):
        if self.confirmed_at and self.confirmed_at < datetime.now():
            return True
        return False

    @property
    def is_anonymous(self):
        return False

    @property
    def is_staff(self):
        return self.staff_id is not None

    def get_id(self):
        return self.openid if self.openid else self.mobile if self.mobile else self.email

    def is_active(self):
        return self.active

    def is_authenticated(self):
        #return self.authenticated
        return True

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed_at = datetime.now();
        db.session.add(self)
        return True

    def ping(self):
        pass
        #self.last_seen = datetime.now()
        #db.session.add(self)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_authenticated(self):
        return False

login_manager.anonymous_user = AnonymousUser

class Supplier(db.Model): # 存储供应商和物流商信息
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    contact_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, index=True, nullable=False)
    ali = db.Column(db.String(128), unique=True, index=True)
    qq = db.Column(db.String(16), unique=True, index=True)
    weixin = db.Column(db.String(128), unique=True, index=True)
    url = db.Column(db.String(1024), unique=True, index=True)
    email = db.Column(db.String(128), unique=True, index=True)
    telephone = db.Column(db.String(15), unique=True, index=True)
    address = db.Column(db.String(512))
    address2 = db.Column(db.String(512))
    is_supplier = db.Column(db.Boolean, default=True) # 是否是供应商，默认是
    is_freighter = db.Column(db.Boolean, default=False) # 是否是物流公司，默认不是
    description = db.Column(db.Text)

    products = db.relationship('ProductSupplier', back_populates='supplier')

    def __init__(self, name, contact, mobile, ali=None, qq=None,
                 weixin=None, url=None, email=None, telephone=None,
                 address=None, is_supplier=True, is_freighter=False,
                 description=None):
        self.name = name
        self.contact = contact
        self.mobile = mobile

    def save(self):
        db.session.add(self)
        db.session.flush()

    def __repr__(self):
        return self.name

class ProductCategory(db.Model):
    __tablename__ = 'product_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    english_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    slug = db.Column(db.String(128), unique=True, index=True, nullable=True)
    is_available_on_web = db.Column(db.Boolean, default=True) # web端显示标志
    is_available_on_pos = db.Column(db.Boolean, default=True) # POS端显示标志
    is_deleted = db.Column(db.Boolean, default=False) # 删除标志
    to_point = db.Column(db.Boolean, default=False) # 是否参与积分
    description = db.Column(db.Text)

    def __init__(self, name, english_name, description=None):
        self.name = name
        self.english_name = english_name

    def __repr__(self):
        return self.name

    def to_json(self):
        return {"id": self.id,
                "name": self.name,
                "english_name": self.english_name,
                "description": self.description
                }

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), unique=True, index=True)
    english_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    sequence = db.Column(db.SmallInteger)
    show_in_home = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    products = db.relationship('ProductTag', back_populates='tag')

    def __repr__(self):
        return self.name

class ProductTag(db.Model):
    __tablename__ = 'product_tag'
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)

    product = db.relationship("Product", back_populates="tags")
    tag = db.relationship("Tag", back_populates="products")

    #@property
    #def id(self):
    #    return (self.product_id, self.tag_id)

    @property
    def target_id(self):
        return self.tag_id

    def __repr__(self):
        return self.product.name + ':' +self.tag.name

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256), nullable=False, unique=True, index=True)
    name = db.Column(db.String(128), unique=True, index=True)
    english_name = db.Column(db.String(128), unique=True, index=True)
    #cover = db.Column(db.String(1024))
    pinyin = db.Column(db.String(128), unique=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'))
    category = db.relationship('ProductCategory',
                         backref=db.backref('products', lazy="dynamic"))
    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'))
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('products', lazy="dynamic"))
    original_price = db.Column(db.Numeric(7,2), default=0.0) # 原价
    price = db.Column(db.Numeric(7,2), default=0.0) # 现价
    #spec = db.Column(db.String(32))
    member_price = db.Column(db.Numeric(7,2), default=0.0) # 会员价
    stock = db.Column(db.Numeric(7,2), default=0.0) # 库存
    size = db.Column(db.String(64)) # 重量/尺寸
    is_available_on_web = db.Column(db.Boolean, default=True) # web端显示标志
    is_available_on_pos = db.Column(db.Boolean, default=True) # POS端显示标志
    is_deleted = db.Column(db.Boolean, default=False) # 删除标志
    to_point = db.Column(db.Boolean, default=False) # 是否参与积分
    pre_order_hours = db.Column(db.Integer, default=24) # 需要预定的时间，一般为提前一天预定
    pub_date = db.Column(db.DateTime, default=datetime.now)
    #unit = db.Column(db.String(8))
    summary = db.Column(db.Text)
    description = db.Column(db.Text)

    #tag_id = db.Column(db.Integer, db.ForeignKey('product_tag.id'))
    tags = db.relationship('ProductTag',
                         back_populates='product')
    suppliers = db.relationship('ProductSupplier',
                        back_populates='product')
    parameters = db.relationship('ProductParameter',
                        back_populates='product')
    tickets = db.relationship('TicketProduct',
                        back_populates='product')
    images = db.relationship('ProductImage',
                        back_populates='product')
    #specifications = db.relationship('ProductSpecification',
    #                    back_populates='product')

    dragons = db.relationship('DragonProduct', back_populates="product")

    def __repr__(self):
        return self.name

    def to_json(self):
        images = []
        banner = None
        for i in self.images:
            if i.image.category and i.image.category.name == 'banner':
                banner = i.image.name + '.' + i.image.ext
            images.append(i.to_json())

        if not banner and self.images:
            banner = self.images[0].image.name + '.' + self.images[0].image.ext
        d = {
                'id': self.id,
                'code': self.code,
                'name': self.name,
                'english_name': self.english_name,
                'original_price': float(self.original_price),
                'price': float(self.price),
                'member_price': float(self.member_price),
                'size': self.size,
                'stock': float(self.stock),
                'banner': banner,
                'images': images,
                'summary': self.summary,
                'desc': self.description,
                'tags': [pt.tag.name for pt in self.tags]
                }

        return d

class BakeryCategory(db.Model):
    __tablename__ = 'bakery_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    english_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return self.name

class BakeryClass(db.Model):
    __tablename__ = 'bakery_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    description = db.Column(db.Text) # 说明

    members = db.relationship('Bakery',
                        back_populates='bakery_class')

    images = db.relationship('BakeryImage', back_populates='bakery_class')

    category_id = db.Column(db.Integer, db.ForeignKey('bakery_category.id'))
    category = db.relationship('BakeryCategory',
                         backref=db.backref('classes', lazy="dynamic"))
    #specifications = db.relationship('ProductSpecification',

class BakeryTime(db.Model):
    __tablename__ = 'bakery_time'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime) # 上课开始时间
    required_time = db.Column(db.SmallInteger, default=45) # 上课所需时间

    original_price = db.Column(db.Numeric(7,2), default=0) # 课程原始价格
    price = db.Column(db.Numeric(7,2), default=0) #课程现在价格

    bakery_class_id = db.Column(db.Integer, db.ForeignKey('bakery_class.id'))
    bakery_class = db.relationship('BakeryClass',
                         backref=db.backref('bakerytimes', lazy="dynamic"))

class Bakery(db.Model):
    __tablename__ = 'bakery'
    id = db.Column(db.Integer, primary_key=True)

    bakery_class_id = db.Column(db.Integer, db.ForeignKey('bakery_class.id'))
    userauth_id = db.Column(db.Integer, db.ForeignKey('userauth.id'))
    start_time = db.Column(db.DateTime) # 上课开始时间
    required_time = db.Column(db.SmallInteger, default=45) # 上课所需时间

    expires_at = db.Column(db.DateTime) # 课程过期时间

    bakery_class = db.relationship("BakeryClass", back_populates="members")
    member = db.relationship("UserAuth", back_populates="bakery_classes")


class ParameterCategory(db.Model):
    __tablename__ = 'parameter_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    #parameter_type = db.Column(db.String(32)) # 选项的类型，比如String, Integer

    def __repr__(self):
        return self.name

class Parameter(db.Model):
    __tablename__ = 'parameter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    size = db.Column(db.Integer) # 蛋糕尺寸大小，单位cm
    share_min = db.Column(db.Integer) # 可以分享的最小人数
    share_max = db.Column(db.Integer) # 可以分享的最大人数
    tableware = db.Column(db.Integer) # 包含餐具个数
    pre_order_time = db.Column(db.Integer) # 需提前预定时间，单位hour
    category_id = db.Column(db.Integer, db.ForeignKey('parameter_category.id'))

    category = db.relationship('ParameterCategory',
            backref=db.backref('parameters', lazy='dynamic'))
    products = db.relationship('ProductParameter',
                        back_populates='parameter')

    def __repr__(self):
        return self.name

class ProductParameter(db.Model):
    __tablename__ = 'product_parameter'
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    parameter_id = db.Column(db.Integer, db.ForeignKey('parameter.id'), primary_key=True)
    #string_value = db.Column(db.String(2048))
    plus_price = db.Column(db.Numeric(7,2), default=0) # 在产品价格的基础上做加法, 这样有个parameter的时候都做加法即可
    stock = db.Column(db.Numeric(7,2), default=0) # 库存

    product = db.relationship("Product", back_populates="parameters")
    parameter = db.relationship('Parameter', back_populates='products')

    @property
    def target_id(self):
        return self.parameter_id

    def __repr__(self):
        return ': '.join([self.parameter.name, str(self.plus_price)])

    def to_json(self):
        return {
                "plus_price": float(self.plus_price),
                "stock": float(self.stock)
                }


class ProductSupplier(db.Model):
    __tablename__ = 'product_supplier'
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), primary_key=True)
    price = db.Column(db.Numeric(7,2), default=0) # 供货商提供的价格，供货商价格有差异
    description = db.Column(db.Text)

    product = db.relationship("Product", back_populates="suppliers")
    supplier = db.relationship("Supplier", back_populates="products")

    @property
    def target_id(self):
        return self.supplier_id


# order table
class Ticket(db.Model):
    __tablename__ = 'ticket'
    code = db.Column(db.String(32), primary_key=True, index=True) # 订单编号
    payment_code = db.Column(db.String(128), nullable=True) # 第三方支付平台订单编号
    #cashier = models.ForeignKey(Staff) # 收银员
    product_amount = db.Column(db.Integer, default=1) # 商品总数量
    original_price = db.Column(db.Numeric(7,2), default=0) # 订单原始总价格
    real_price = db.Column(db.Numeric(7,2), default=0) # 订单现在总价格
    #off = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=original_price-real_price
    #discount = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=real_price/original_price
    bonus_balance = db.Column(db.Numeric(7,2), default=0) # 赠送金额，充值的时候会产生赠送金额
    type = db.Column(db.SmallInteger, default=0) # 消费方式, 0: 消费, 1: 充值, 2: 退货, 3: 反结账, 4: 退卡
    pending_time = db.Column(db.DateTime) # 挂单时间
    occurred_time = db.Column(db.DateTime, default=datetime.now) # 订单时间
    required_datetime = db.Column(db.DateTime) # 使用日期和时间
    candle = db.Column(db.String(64)) # 蜡烛

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('tickets', lazy="dynamic"))

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True) # 会员消费
    member = db.relationship('Member',
                         backref=db.backref('tickets', lazy="dynamic"))

    address_id = db.Column(db.Integer, db.ForeignKey('ticket_address.id'), nullable=True) # 配送地址
    address = db.relationship('TicketAddress')

    products = db.relationship('TicketProduct', back_populates='ticket')
    payments = db.relationship('TicketPayment', back_populates='ticket')
    pay_time = db.Column(db.DateTime) # 支付时间

    note = db.Column(db.Text)

    def __repr__(self):
        return self.code


class TicketAddress(db.Model):
    __tablename__ = 'ticket_address'
    id = db.Column(db.Integer, primary_key=True)
    contact_name = db.Column(db.String(128)) # 联系人或者收货人姓名/紧急联系人姓名
    mobile = db.Column(db.String(16))
    address = db.Column(db.String(256))

    delivery_time = db.Column(db.DateTime) # 配送日期
    arrived_time = db.Column(db.DateTime) # 签收日期


class TicketProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_code = db.Column(db.String(64), db.ForeignKey('ticket.code'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    parameters_json = db.Column(db.String(256)) # 交易时所选的属性名称，一旦该属性被删，这个可以用来查看订单记录的属性名称
    original_price = db.Column(db.Numeric(7,2), default=0) # 商品原始总价格
    real_price = db.Column(db.Numeric(7,2), default=0) # 商品实际价格
    amount = db.Column(db.Integer, default=1) # 商品总数量
    sale_time = db.Column(db.DateTime, default=datetime.now) # 售卖时间

    product = db.relationship("Product", back_populates="tickets")
    ticket = db.relationship('Ticket', back_populates='products')

    @property
    def parameters(self):
        return json.loads(self.parameters_json)

    @parameters.setter
    def parameters(self, parameters):
        self.parameters_json = json.dumps(parameters)


class TicketPayment(db.Model):
    ticket_code = db.Column(db.String(64), db.ForeignKey('ticket.code'), primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    #balance = db.Column(db.Numeric(7,2), default=0) # 该付款方式，收到的金额
    receive_balance = db.Column(db.Numeric(7,2), default=0) # 收银多少，现金一般会收到整钱，然后找零
    change_balance = db.Column(db.Numeric(7,2), default=0) # 找零多少
    payment_code = db.Column(db.String(64)) # 第三方支付返回的支付码

    ticket = db.relationship('Ticket', back_populates='payments') # 订单
    payment = db.relationship("Payment", back_populates="tickets") # 付款方式


# 每个店的支付方式也有不同
class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    is_change = db.Column(db.Boolean, default=False) # 是否存在找零
    #discount = models.IntegerField(default=100, null=True, blank=True) # 打折费用
    #every = models.DecimalField(max_digits=7, decimal_places=2, default=0, null=True, blank=True) # 满every值减off的钱
    #off = models.DecimalField(max_digits=7, decimal_places=2, default=0, null=True, blank=True) # 
    charge = db.Column(db.Numeric(7,2), default=0) # 手续费
    is_available_on_web = db.Column(db.Boolean, default=True) # web端可用标志
    is_available_on_pos = db.Column(db.Boolean, default=True) # POS端可用标志
    to_point = db.Column(db.Boolean, default=True) # 该支付方式是否积分
    description = db.Column(db.Text)

    tickets = db.relationship('TicketPayment', back_populates='payment')

    def __repr__(self):
        return self.name

class GalleryCategory(db.Model):
    __tablename__ = 'gallery_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    description = db.Column(db.Text) # 图片分类详细描述

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('gallery_categories', lazy="dynamic"))

    def __repr__(self):
        return self.name

class Image(db.Model):
    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True)
    upload_name = db.Column(db.String(128)) # 图片上传时的名字
    name = db.Column(db.String(128)) # 图片存储时的名字
    directory = db.Column(db.String(2048)) # 存储在系统上的相对路径
    ext = db.Column(db.String(8)) # 图片的扩展名，不带.
    title = db.Column(db.String(128)) # 图片主题
    category_id = db.Column(db.Integer, db.ForeignKey('gallery_category.id'))
    category = db.relationship('GalleryCategory',
                         backref=db.backref('images', lazy="dynamic"))
    added_date = db.Column(db.DateTime, default=datetime.now)
    hash_value = db.Column(db.String(64)) # 图片的MD5值
    description = db.Column(db.Text) # 图片详细描述

    products = db.relationship('ProductImage',
                        back_populates='image')

    classes = db.relationship('BakeryImage',
                        back_populates='image')

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('images', lazy="dynamic"))

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'ext': self.ext,
            'hash_value': self.hash_value,
            'type': 'banner' if not self.category else self.category.name,
            'title': self.title,
        }

    def __repr__(self):
        return '.'.join([self.name, self.ext])

# N:N relationship
class ProductImage(db.Model):
    __tablename__ = 'product_image'

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), primary_key=True)
    sequence = db.Column(db.Integer, default=1) # 做为封面的图片，sequence定义为0, 其余为1或者排序
    description = db.Column(db.Text) # 产品图片描述

    product = db.relationship("Product", back_populates="images")
    image = db.relationship('Image', back_populates='products')

    @property
    def target_id(self):
        return self.image_id

    def to_json(self):
        d = self.image.to_json()
        d['seq'] = self.sequence

        return d

    def __repr__(self):
        return "%s - %s" % (self.product_id, self.image_id)

# N:N relationship
class BakeryImage(db.Model):
    __tablename__ = 'bakery_image'

    bakery_class_id = db.Column(db.Integer, db.ForeignKey('bakery_class.id'), primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), primary_key=True)
    sequence = db.Column(db.Integer, default=1) # 做为封面的图片，sequence定义为0, 其余为1或者排序
    description = db.Column(db.Text) # 产品图片描述

    bakery_class = db.relationship("BakeryClass", back_populates="images")
    image = db.relationship('Image', back_populates='classes')

    def __repr__(self):
        return "%s - %s" % (self.product_id, self.image_id)

class ShoppingCart(db.Model):
    __tablename__ = 'shopping_cart'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    parameters = db.Column(db.Text)

    product = db.relationship('Product')
    member = db.relationship('Member')

    def __init__(self, member, product, parameters):
        self.member = member
        self.product = product
        self.parameters = jsonify(parameters)

    def __repr__(self):
        return "shopping cart"

@login_manager.user_loader
def user_loader(condition):
    if not condition:
        return None
    user = UserAuth.query.filter(or_(UserAuth.email==condition,
                                     UserAuth.mobile==condition,
                                     UserAuth.openid==condition)).first()

    return user

class WeixinConfig(db.Model):
    __tablename__ = 'weixin_config'
    id = db.Column(db.Integer, primary_key=True)

class WeixinConfigAdmin(db.Model):
    __tablename__ = 'weixin_admin'
    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.Integer, db.ForeignKey('weixin_config.id'))
    openid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin

    config = db.relationship('WeixinConfig', backref=db.backref('WeixinConfig', lazy='dynamic'))


dragon_address_relation = db.Table('dragon_address_relation', db.Model.metadata,
        db.Column('dragon_id', db.Integer, db.ForeignKey('dragon.id')),
        db.Column('dragon_address_id', db.Integer, db.ForeignKey('dragon_address.id'))
    )

class Dragon(db.Model):
    __tablename__ = 'dragon'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False) # used in weixin
    bind_flag = db.Column(db.Boolean, default=True) # true-捆绑销售
    member_flag = db.Column(db.Boolean, default=True) # true-允许使用会员卡
    delivery_fee = db.Column(db.Numeric(5,2), default=0.0) # 最低基础运费
    from_time = db.Column(db.DateTime, default=datetime.now, nullable=False) # 提货开始时间
    to_time = db.Column(db.DateTime, default=datetime.now, nullable=False) # 提货结束时间
    last_order_time = db.Column(db.DateTime, default=datetime.now) # 截单时间
    publish_time = db.Column(db.DateTime, default=datetime.now)

    delivery_method = db.Column(db.SmallInteger, default=2) # 0-免费快递;1-固定快递费;2-根据路程远近
    prepay_flag= db.Column(db.SmallInteger, default=1) # 0-取货付款;1-先付款
    description = db.Column(db.Text) # 详细描述

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('dragons', lazy="dynamic"))
    owner_id = db.Column(db.Integer, db.ForeignKey('member_openid.id'), nullable=False)
    owner = db.relationship('MemberOpenID',
                         backref=db.backref('dragons', lazy="dynamic"))

    products = db.relationship('DragonProduct', back_populates="dragon")
    addresses = db.relationship('DragonAddress', secondary=dragon_address_relation)
    orders = db.relationship('DragonOrder', back_populates='dragon', order_by="desc(DragonOrder.seq)")

    def __init__(self, name, openid):
        self.name = name
        owner = MemberOpenID.query.filter_by(openid=openid).first_or_404()
        self.owner = owner
        self.owner_id = owner.id

    def save(self):
        db.session.add(self)
        db.session.commit()

    def remove(self):
        db.session.delete(self)
        db.session.commit()

    def to_json(self):
        orders = []
        now = datetime.now()
        for o in self.orders:
            if o.pay_time and o.pay_time < now:
                orders.append(o.to_json())

        return {
            'code': self.id,
            'name': self.name,
            'delivery_method': self.delivery_method,
            'delivery_fee': float(self.delivery_fee) if self.delivery_fee else 0,
            'bind_flag': self.bind_flag,
            'member_flag': self.member_flag,
            #'from_date': self.from_time.strftime(''),
            'from_time': self.from_time.strftime('%Y-%m-%d %H:%M'),
            #'to_date': self.to_time.strftime('%Y-%m-%d'),
            'to_time': self.to_time.strftime('%Y-%m-%d %H:%M'),
            'last_order_time': self.last_order_time.strftime('%Y-%m-%d %H:%M'),
            'publish_time': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'products': [p.to_json() for p in self.products],
            'addresses': [a.to_json() for a in self.addresses],
            'orders': orders,
            'description': self.description
        }


class DragonProduct(db.Model):
    __tablename__ = 'dragon_product'

    id = db.Column(db.Integer, primary_key=True)
    dragon_id = db.Column(db.Integer, db.ForeignKey('dragon.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    price = db.Column(db.Numeric(7,2), default=0.0) # 现价
    sold = db.Column(db.Integer, default=1) # 商品总数量
    total = db.Column(db.Integer, default=1) # 商品总数量

    product = db.relationship("Product", back_populates="dragons")
    dragon = db.relationship("Dragon", back_populates="products")
    orders = db.relationship('DragonOrderProduct', back_populates='product')

    description = db.Column(db.Text) # 详细描述

    __table_args__ = (db.UniqueConstraint('dragon_id', 'product_id', name='dragon_product_uc'),)

    def __init__(self, dragon_id, product_id):
        self.dragon_id = dragon_id
        self.product_id = product_id

        db.session.add(self)

    def to_json(self):
        d = self.product.to_json()
        d['dragon_price'] = float(self.price)
        d['dragon_sold'] = self.sold
        d['dragon_total'] = self.total

        return d

## NO_PAY = 0
## CASH_PAY = 1
## VALUE_CARD_PAY = 2 # 储值卡
## WECHAT_PAY = 4
## ALI_PAY = 8

class DragonOrder(db.Model):
    __tablename__ = 'dragon_order'

    code = db.Column(db.String(32), primary_key=True, index=True) # 订单编号
    payment_code = db.Column(db.String(128), nullable=True) # 第三方支付平台订单编号
    #cashier = models.ForeignKey(Staff) # 收银员
    original_price = db.Column(db.Numeric(7,2), default=0) # 订单原始总价格
    real_price = db.Column(db.Numeric(7,2), default=0) # 订单现在总价格
    seq = db.Column(db.Integer)

    member_id = db.Column(db.Integer, db.ForeignKey('member_openid.id'), nullable=False) # 会员消费
    dragon_id = db.Column(db.Integer, db.ForeignKey('dragon.id'), nullable=False)
    delivery_address_id = db.Column(db.Integer, db.ForeignKey('delivery_address.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('dragon_address.id'))

    occurred_time = db.Column(db.DateTime, default=datetime.now) # 订单时间
    #payment_method = db.Column(ENUM("CASH", "VALUE_CARD", "WECHAT", "ALIPAY", name="payment_enum", metadata=db.metadata)) # 支付方式
    payment = db.Column(db.Integer, default=0) # 支付方式
    pay_time = db.Column(db.DateTime) # 支付时间
    prepay_id = db.Column(db.String(128), nullable=True) # 微信预支付ID
    prepay_id_expires = db.Column(db.BigInteger) # 微信预支付ID过期时间

    note = db.Column(db.Text)

    dragon = db.relationship('Dragon', back_populates='orders')
    member = db.relationship('MemberOpenID', back_populates='orders')
    products = db.relationship('DragonOrderProduct', back_populates='order')

    delivery_address = db.relationship('DeliveryAddress', back_populates='orders')
    address = db.relationship('DragonAddress', back_populates='orders')

    __table_args__ = (db.UniqueConstraint('member_id', 'dragon_id', name='dragon_member_uc'),)

    def __init__(self, code):
        self.code = code

    def save(self):
        db.session.add(self)
        db.session.commit()

    def withdraw(self):
        for p in self.products:
            db.session.delete(p)

        db.session.delete(self)

        db.session.commit()

    def to_json(self):
        d = {
                'seq': self.seq,
                'code': self.code,
                'original_price': float(self.original_price),
                'price': float(self.real_price),
                'products': [p.to_json() for p in self.products],
                'to_delivery': not self.address,
                'address': self.address.to_json() if self.address else self.delivery_address.to_json(),
                'dragon_id': self.dragon_id,
                'note': self.note,
                'prepay_id': self.prepay_id,
                'paid': self.payment_code is not None and self.pay_time is not None,
                'payment': self.payment,
                #'delivery_info': self.delivery_address.to_json()
                }

        if self.member:
            d['member'] = self.member.to_json()

        return d

    def __repr__(self):
        return self.code


class DragonAddress(db.Model):
    __tablename__ = 'dragon_address'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(512))
    is_default = db.Column(db.Boolean, default=False)
    from_time = db.Column(db.String(8))
    to_time = db.Column(db.String(8))

    orders = db.relationship('DragonOrder', back_populates='address')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_json(self):
        return {'code': self.id,
                'address': self.address,
                'from_time': self.from_time,
                'to_time': self.to_time,
                'is_default': self.is_default
                }

    def __repr__(self):
        return self.address


class DragonOrderProduct(db.Model):
    __tablename__ = 'dragon_order_product'

    dragon_order_code = db.Column(db.String(32), db.ForeignKey('dragon_order.code'), primary_key=True)
    dragon_product_id = db.Column(db.Integer, db.ForeignKey('dragon_product.id'), primary_key=True)

    product = db.relationship('DragonProduct', back_populates='orders')
    order = db.relationship('DragonOrder', back_populates='products')

    amount = db.Column(db.Integer, default=1) # the number of products in order

    def to_json(self):
        d = self.product.to_json()
        d['amount'] = self.amount

        return d
