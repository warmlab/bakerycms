from datetime import datetime
#import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
#from markdown import markdown
#import bleach
from flask import current_app#, url_for
from flask import json, jsonify
from flask_login import UserMixin, AnonymousUserMixin

from sqlalchemy import or_
#from .exceptions import ValidationError
from . import db, login_manager


class Shoppoint(db.Model):
    __tablename__ = 'shoppoint'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, index=True)
    login_name = db.Column(db.String(64))
    name = db.Column(db.String(128))
    contact = db.Column(db.String(128)) # 店长或者负责人
    phone = db.Column(db.String(16)) # 店内固定电话
    mobile = db.Column(db.String(16))
    address = db.Column(db.String(1024))
    password = db.Column(db.String(64))
    weixin_token = db.Column(db.String(32))
    description = db.Column(db.Text)

    def __repr__(self):
        return self.name


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
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    email = db.Column(db.String(64), unique=True, index=True)
    nickname = db.Column(db.String(128)) # 会员姓名
    to_point = db.Column(db.Boolean, default=True) # 该会员是否参与积分
    points = db.Column(db.Integer, default=0) # 积分
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    member_end = db.Column(db.DateTime, default=None)
    avatar_hash = db.Column(db.String(32)) # 头像
    about_me = db.Column(db.Text)

    grade_id = db.Column(db.Integer, db.ForeignKey('member_grade.id'))
    grade = db.relationship('MemberGrade',
                         backref=db.backref('members', lazy='dynamic'))

    weixin_openid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin
    weixin_unionid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin

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
    staff_since = db.Column(db.DateTime, default=datetime.utcnow)
    staff_end = db.Column(db.DateTime, default=None)

    def can(self, permission):
        return True # TODO

class UserAuth(db.Model, UserMixin):
    __tablename__ = 'userauth'
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    email = db.Column(db.String(64), unique=True, index=True)
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    password_hash = db.Column(db.String(128), nullable=False)
    #reset_password_token = db.Column(db.String(128), nullable=False)
    confirmed_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=False)

    # Relationships
    staff_id = db.Column(db.Integer(), db.ForeignKey('staff.id', ondelete='CASCADE'))
    staff = db.relationship('Staff', uselist=False, foreign_keys=staff_id)
    member_id = db.Column(db.Integer(), db.ForeignKey('member.id', ondelete='CASCADE'))
    member = db.relationship('Member', uselist=False, foreign_keys=member_id)

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('userauth', lazy="dynamic"))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def confirmed(self):
        if self.confirmed_at and self.confirmed_at < datetime.utcnow():
            return True
        return False

    def get_id(self):
        return self.mobile if self.mobile else self.email

    def is_active(self):
        return self.active

    def is_authenticated(self):
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
        self.confirmed_at = datetime.utcnow();
        db.session.add(self)
        return True

    def ping(self):
        pass
        #self.last_seen = datetime.utcnow()
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
    description = db.Column(db.Text)

    def __init__(self, name, english_name, description=None):
        self.name = name
        self.english_name = english_name

    def __repr__(self):
        return self.name


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
    original_price = db.Column(db.Numeric(7,2), default=0.0) # 原价
    price = db.Column(db.Numeric(7,2), default=0.0) # 现价
    member_price = db.Column(db.Numeric(7,2), default=0.0) # 会员价
    stock = db.Column(db.Numeric(7,2), default=0.0) # 库存
    is_available_on_web = db.Column(db.Boolean, default=True) # web端显示标志
    is_available_on_pos = db.Column(db.Boolean, default=True) # POS端显示标志
    is_deleted = db.Column(db.Boolean, default=False) # 删除标志
    to_point = db.Column(db.Boolean, default=False) # 是否参与积分
    pub_date = db.Column(db.DateTime, default=datetime.utcnow)
    #unit = db.Column(db.String(8))
    description = db.Column(db.Text)

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

    def __init__(self, code, name, english_name, pinyin, category,
                 original_price, price, member_price, stock,
                 is_available_on_web=True, is_available_on_pos=True,
                 to_point=True, pub_date=None, description=None):
        self.code = code
        self.name = name
        self.english_name = english_name
        self.pinyin = pinyin
        self.category = category
        self.original_price = original_price
        self.price = price
        self.member_price = member_price
        self.stock = stock
        self.is_available_on_web = is_available_on_web
        self.is_available_on_pos = is_available_on_pos
        self.is_deleted = False
        self.to_point = to_point
        if pub_date == None:
            self.pub_date = datetime.utcnow()
        else:
            self.pub_date = pub_date
        self.description = description

    def __repr__(self):
        return self.name


class ParameterCategory(db.Model):
    __tablename__ = 'parameter_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    #parameter_type = db.Column(db.String(32)) # 选项的类型，比如String, Integer

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class Parameter(db.Model):
    __tablename__ = 'parameter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('parameter_category.id'))

    category = db.relationship('ParameterCategory',
            backref=db.backref('parameters', lazy='dynamic'))
    products = db.relationship('ProductParameter',
                        back_populates='parameter')

    def __init__(self, name, parameter_category):
        self.name = name
        self.parameter_category = parameter_category

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

    def __init__(self, product, parameter, plus_price, stock):
        self.product = product
        self.parameter = parameter
        self.plus_price = plus_price
        self.stock = stock

    def __repr__(self):
        return str(self.plus_price)
    

class ProductSupplier(db.Model):
    __tablename__ = 'product_supplier'
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), primary_key=True)
    price = db.Column(db.Numeric(7,2), default=0) # 供货商提供的价格，供货商价格有差异
    description = db.Column(db.Text)

    product = db.relationship("Product", back_populates="suppliers")
    supplier = db.relationship("Supplier", back_populates="products")


# order table
class Ticket(db.Model):
    __tablename__ = 'ticket'
    code = db.Column(db.String(64), primary_key=True, index=True) # 订单编号
    payment_code = db.Column(db.String(64), nullable=True) # 第三方支付平台订单编号
    #cashier = models.ForeignKey(Staff) # 收银员
    product_amount = db.Column(db.Integer, default=1) # 商品总数量
    original_price = db.Column(db.Numeric(7,2), default=0) # 订单原始总价格
    real_price = db.Column(db.Numeric(7,2), default=0) # 订单现在总价格
    #off = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=original_price-real_price
    #discount = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=real_price/original_price
    bonus_balance = db.Column(db.Numeric(7,2), default=0) # 赠送金额，充值的时候会产生赠送金额
    type = db.Column(db.SmallInteger, default=0) # 消费方式, 0: 消费, 1: 充值, 2: 退货, 3: 反结账, 4: 退卡
    pending_time = db.Column(db.DateTime) # 挂单时间
    occurred_time = db.Column(db.DateTime, default=datetime.utcnow) # 订单时间
    required_datetime = db.Column(db.DateTime) # 使用日期和时间

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
    sale_time = db.Column(db.DateTime, default=datetime.utcnow) # 售卖时间

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


class Image(db.Model):
    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True)
    upload_name = db.Column(db.String(128)) # 图片上传时的名字
    name = db.Column(db.String(128)) # 图片存储时的名字
    directory = db.Column(db.String(2048)) # 存储在系统上的相对路径
    ext = db.Column(db.String(8)) # 图片的扩展名，不带.
    title = db.Column(db.String(128)) # 图片主题
    #category_id = db.Column(db.Integer, db.ForeignKey('gallery_category.id'))
    #category = db.relationship('GalleryCategory',
    #                     backref=db.backref('images', lazy="dynamic"))
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text) # 图片详细描述

    products = db.relationship('ProductImage',
                        back_populates='image')

    def __init__(self, upload_name, name, directory, ext, title=None, description=None):
        self.upload_name = upload_name
        self.name = name
        self.directory = directory
        self.ext = ext
        self.title = title
        self.description = description

    def __repr__(self):
        return self.url

# N:N relationship
class ProductImage(db.Model):
    __tablename__ = 'product_image'

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), primary_key=True)
    sequence = db.Column(db.Integer, default=1) # 做为封面的图片，sequence定义为0, 其余为1或者排序
    description = db.Column(db.Text) # 产品图片描述

    product = db.relationship("Product", back_populates="images")
    image = db.relationship('Image', back_populates='products')

    def __init__(self, product, image, sequence=1, description=None):
        self.product = product
        self.image = image
        self.sequence = sequence
        self.description = description

    def __repr__(self):
        return "%s - %s" % (self.product_id, self.image_id)

class ShoppingCart(db.Model):
    __tablename__ = 'shopping_cart'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    parameters = db.Column(db.String)

    product = db.relationship('Product')
    member = db.relationship('Member')

    def __init__(self, member, product, parameters):
        self.member = member
        self.product = product
        self.parameters = jsonify(parameters)

    def __repr__(self):
        return "shopping cart"

@login_manager.user_loader
def user_loader(email):
    user = UserAuth.query.filter(or_(UserAuth.email==email, UserAuth.mobile==email)).first()
    if not user:
        return None

    return user
