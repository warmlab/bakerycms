from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
#from markdown import markdown
#import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
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


class MemberAddress(db.Model):
    __tablename__ = 'member_address'
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

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    member = db.relationship('Member',
                         backref=db.backref('addresses', lazy="dynamic"))

    #shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    #shoppoint = db.relationship('Shoppoint',
    #                     backref=db.backref('addresses', lazy="dynamic"))

    #staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    #staff = db.relationship('Staff',
    #                     backref=db.backref('addresses', lazy="dynamic"))


class MemberGrade(db.Model): # 会员等级或分类
    __tablename__ = 'member_grade'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    discount = db.Column(db.Integer, default=100) # 100表示不打折, 80表示8折
    to_point = db.Column(db.Boolean, default=True) # 该类会员是否参与积分
    description = db.Column(db.Text)

    def __repr__(self):
        return self.name

class WeixinMember(db.Model):
    __tablename__ = 'weixin_member'

    openid = db.Column(db.String(64), primary_key=True) # used in weixin
    unionid = db.Column(db.String(64), unique=True, nullable=True) # used in weixin
    subscribe = db.Column(db.Boolean)
    subscribe_time = db.Column(db.DateTime)
    nickname = db.Column(db.String(64))
    sex = db.Column(db.SmallInteger)
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    province = db.Column(db.String(64))
    language = db.Column(db.String(64))
    headimgurl = db.Column(db.String(2048))
    remark = db.Column(db.String(64))
    groupid = db.Column(db.String(64))
    tagid = db.Column(db.BigInteger)

    member = db.relationship("Member", uselist=False, back_populates="weixin_member")

    def __init__(self, openid, unionid, subscribe, nickname, sex, city, country, province, headimgurl,
                 remark=None, groupid=None, tagid=None, language=None, subscribe_time=None):
        self.openid = openid
        self.unionid = unionid 
        self.subscribe = subscribe 
        self.subscribe_time = subscribe_time 
        self.nickname = nickname 
        self.sex = sex 
        self.city = city 
        self.country = country 
        self.province = province 
        self.language = language 
        self.headimgurl = headimgurl 
        self.remark = remark 
        self.groupid = groupid 
        self.tagid = tagid 

class Member(UserMixin, db.Model):
    __tablename__ = 'member'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, index=True) # 实体会员卡的卡面卡号，没有实体卡，可以使用用户名
    email = db.Column(db.String(64), unique=True, index=True)
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    member_name = db.Column(db.String(64), unique=True, index=True) # 会员登录号
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(128), index=True) # 会员姓名
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    to_point = db.Column(db.Boolean, default=True) # 该会员是否参与积分
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    member_end = db.Column(db.DateTime, default=None)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32)) # 头像

    grade_id = db.Column(db.Integer, db.ForeignKey('member_grade.id'))
    grade = db.relationship('MemberGrade',
                         backref=db.backref('members', lazy='dynamic'))

    weixin_openid = db.Column(db.String(64), db.ForeignKey('weixin_member.openid'))
    weixin_member = db.relationship("WeixinMember", back_populates='member')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return name

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
    parameter_category_id = db.Column(db.Integer, db.ForeignKey('parameter_category.id'))

    parameter_category = db.relationship('ParameterCategory',
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
    code = db.Column(db.String(64), primary_key=True, index=True) # 订单编号
    payment_code = db.Column(db.String(64), nullable=True) # 第三方支付平台订单编号
    #cashier = models.ForeignKey(Staff) # 收银员
    product_amount = db.Column(db.Integer, default=1) # 商品总数量
    original_cost = db.Column(db.Numeric(7,2), default=0) # 订单原始总价格
    real_cost = db.Column(db.Numeric(7,2), default=0) # 订单现在总价格
    #off = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=original_cost-real_cost
    #discount = db.Column(db.Numeric(7,2), default=0) # 订单优惠金额，该项=real_cost/original_cost
    bonus_balance = db.Column(db.Numeric(7,2), default=0) # 赠送金额，充值的时候会产生赠送金额
    type = db.Column(db.SmallInteger, default=0) # 消费方式, 0: 消费, 1: 充值, 2: 退货, 3: 反结账, 4: 退卡
    pending_time = db.Column(db.DateTime, default=datetime.utcnow) # 挂单时间
    occurred_time = db.Column(db.DateTime, default=datetime.utcnow) # 订单时间

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('tickets', lazy="dynamic"))

    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True) # 会员消费
    member = db.relationship('Member',
                         backref=db.backref('tickets', lazy="dynamic"))

    products = db.relationship('TicketProduct', back_populates='ticket')
    payments = db.relationship('TicketPayment', back_populates='ticket')

    def __init__(self, shoppoint, product_amount, original_cost, real_cost, bonus_balance=0, type=0, Member=None):
        self.product_amount = product_amount
        self.original_cost = original_cost
        self.real_cost = real_cost

    def __repr__(self):
        return self.code


class TicketProduct(db.Model):
    #id = db.Column(db.Integer, primary_key=True)
    ticket_code = db.Column(db.String(64), db.ForeignKey('ticket.code'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    original_cost = db.Column(db.Numeric(7,2), default=0) # 商品原始总价格
    real_cost = db.Column(db.Numeric(7,2), default=0) # 商品原始总价格
    product_amount = db.Column(db.Integer, default=1) # 商品总数量
    cost = db.Column(db.Numeric(7,2), default=0) # 商品总成本
    sale_time = db.Column(db.DateTime, default=datetime.utcnow) # 售卖时间

    product = db.relationship("Product", back_populates="tickets")
    ticket = db.relationship('Ticket', back_populates='products')


class TicketPayment(db.Model):
    ticket_code = db.Column(db.String(64), db.ForeignKey('ticket.code'), primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    #balance = db.Column(db.Numeric(7,2), default=0) # 该付款方式，收到的金额
    receive_balance = db.Column(db.Numeric(7,2), default=0) # 收银多少，现金一般会收到整钱，然后找零
    change_balance = db.Column(db.Numeric(7,2), default=0) # 找零多少

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

    def __init__(self, name, is_change=False, charge=0,
                 is_available_on_web=True,
                 is_available_on_pos=True, description=None):
        self.name = name
        self.is_change = is_change
        self.charge = charge
        self.is_available_on_web = is_available_on_web
        self.is_available_on_pos = is_available_on_pos
        self.description = description

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
        return self.description


"""

class GalleryCategory(db.Model):
    __tablename__ = 'gallery_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    english_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    description = db.Column(db.Text)

    def __init__(self, name, english_name, description=None):
        self.name = name
        self.english_name = english_name

    def __repr__(self):
        return self.name

class RestockHistory(db.Model):
    __tablename__ = 'restock_history'
    order_number = db.Column(db.String(64), primary_key=True)
    order_time = db.Column(db.DateTime, default=datetime.utcnow) # 订货时间

    shoppoint_id = db.Column(db.Integer, db.ForeignKey('shoppoint.id'), nullable=True)
    shoppoint = db.relationship('Shoppoint',
                         backref=db.backref('restock_histories', lazy="dynamic"))

class RestockDetail(db.Model):
    __tablename__ = 'restock_detail'
    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('restock_history.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    price = db.Column(db.Numeric(7,2), default=0) # 该次订货，商品价格，会遇到一些打折商品
    arrived_time = db.Column(db.DateTime, default=datetime.utcnow) # 到货时间
    description = db.Column(db.Text)

    product = db.relationship("Product", back_populates="suppliers")
    supplier = db.relationship("Supplier", back_populates="products")


class ProductSpecification(db.Model):
    __tablename__ = 'product_specification'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    specification_id = db.Column(db.Integer, db.ForeignKey('specification.id'))
    #supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    restock_price = db.Column(db.Numeric(7,2), default=0.0)
    original_price = db.Column(db.Numeric(7,2), default=0.0)
    price = db.Column(db.Numeric(7,2), default=0.0)
    member_price = db.Column(db.Numeric(7,2), default=0.0)
    stock = db.Column(db.Numeric(7,2), default=0.0) # 库存
    is_available = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

    product = db.relationship("Product", back_populates="specifications")
    specification = db.relationship('Specification', back_populates='products')
    #supplier = db.relationship('Supplier', back_populates='products')

    def __init__(self, product, specification, restock_price, price,
            old_price=0.0, member_price=0.0, stock=0.0,
            is_available=True, is_deleted=True, description=None):
        self.product = product
        self.specification = specification
        self.restock_price = restock_price
        self.price = price
        self.old_price = old_price
        self.member_address = member_price
        self.stock = stock
        self.is_available = is_available
        self.is_deleted = is_deleted
        self.description = description

class Specification(db.Model):
    __tablename__ = 'specification'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True)
    amount = db.Column(db.Numeric(7,2), default=0.0) # 规格中含有的克数或者ml数
    unit = db.Column(db.String(8))
    description = db.Column(db.Text)

    products = db.relationship('ProductSpecification',
                        back_populates='specification')

    def __init__(self, name, amount, unit=None, description=None):
        self.name = name
        self.amount = amount
        self.unit = unit
        self.description = description

    def __repr__(self):

class Staff(UserMixin, db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    mobile = db.Column(db.String(16), unique=True, index=True) #手机号码
    staff_name = db.Column(db.String(64), unique=True, index=True) # 登录名称
    openid = db.Column(db.String(64), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    staff_since = db.Column(db.DateTime, default=datetime.utcnow)
    staff_end = db.Column(db.DateTime, default=None)
    avatar_hash = db.Column(db.String(32)) # 头像

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

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
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def to_json(self):
        json_user = {
            'url': url_for('rest.get_user', id=self.id, _external=True),
            'staff_name': self.staff_name,
            'staff_since': self.staff_since,
            'last_seen': self.last_seen,
        }
        return json_user

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return Staff.query.get(data['id'])

    def __repr__(self):
        return '<Staff %r>' % self.staff_name
        return self.name
"""
