from flask_admin import Admin

from .views import BakeryView, BakeryModelView
from .views import SaleView, ProductView, ImageView

from ..models import db
from ..models import Product, Tag, Parameter, Image
from ..models import ProductParameter, ProductTag, ProductImage, ProductCategory

admin = Admin(name='小麦芬烘焙工作室',
              index_view=SaleView(
                                  #template="admin/sale.summary.html",
                                  name="销售"),
              template_mode='bootstrap3')

def init_admin(app):
    admin.init_app(app)
    #admin.add_view(SaleView(category="销售", name='单据', url='tickets'))
    #product_models = [Product]

    #for model in product_models:
    admin.add_view(ProductView(Product, db.session, category="产品管理", name="产品"))
    admin.add_view(BakeryModelView(Tag, db.session, category='产品管理', name="标签"))
    admin.add_view(BakeryModelView(ProductCategory, db.session, category='产品管理', name="分类"))

    admin.add_view(ImageView(category="素材管理", name='图片', url='gallery'))
    #admin.add_view(ProductView(name='产品管理', endpoint='product'))
