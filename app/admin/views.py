import os

from datetime import datetime, timedelta

from flask import request, current_app
from flask import flash, redirect, url_for, jsonify

from flask_admin import BaseView, expose
from flask_admin.base import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField
from flask_admin.form.fields import Select2TagsField

import flask_login as login

from wtforms.validators import required
from wtforms.widgets import CheckboxInput
from wtforms.compat import iteritems

from sqlalchemy import text, bindparam
from sqlalchemy import Integer, String

from .forms import CKTextAreaField
from .forms import ImageForm

from ..models import db
from ..models import UserAuth
from ..models import Product, Tag, Parameter, Image, Ticket
from ..models import GalleryCategory

def _get_tag_pk(obj):
    return (obj.product_id, obj.tag_id)

class BakeryView(BaseView):
    def is_accessible(self):
        ua = login.current_user
        if not getattr(ua, 'is_staff', None):
            return False

        return ua.is_active() and ua.is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))


class BakeryModelView(ModelView):
    page_size = 30
    # can_delete = False

    def is_accessible(self):
        ua = login.current_user
        if not getattr(ua, 'is_staff', None):
            return False

        return ua.is_active() and ua.is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))

class ProductView(BakeryModelView):
    column_exclude_list = ('id', 'shoppoint', 'suppliers', 'tickets', 'is_deleted', 'pub_date', 'description')
    column_searchable_list = ['code', 'name', 'english_name', 'pinyin']
    #column_sortable_list = []
    #column_default_sort = None
    column_filters = ['category.name']
    column_default_sort = 'id'
    #edit_form = ProductForm

    form_overrides = {'description':CKTextAreaField}
    form_excluded_columns = ['suppliers', 'is_deleted', 'tickets', 'pub_date']

    form_args = {
            'name': {
                'label': '产品名称',
                'validators': [required()]
            },
            'english_name': {
                'label': '英文名称',
                'validators': [required()]
            },
            'category': {
                'label': '产品分类',
            },
            'tags': {
                'label': '标签',
                'query_factory': lambda: Tag.query.order_by('sequence'),
                'validators': [required()],
            },
            'parameters': {
                'label': '尺寸',
                'query_factory': lambda: Parameter.query.order_by('id')
            },
            'images': {
                'label': '图片',
                'query_factory': lambda: Image.query.all()
            },
        }

    form_widget_args = {
            'category': {
                'class': 'ui dropdown'
            },
            'shoppoint': {
                'class': 'ui dropdown'
            },
            'tags': {
                'class': 'ui basic label checkbox',
            },
            'parameters': {
                'class': 'ui basic label checkbox'
            },
            'images': {
                'class': 'ui medium bordered images',
                'element-type': 'image',
            }
        }

    #tags = Tag.query.all()
    #print (tags)
    #form_choices = {'tags': {
    #form_extra_fields = { 'aaaa': 
    #            QuerySelectMultipleField(
    #                label = '标签',
    #                query_factory = lambda: Tag.query.all(),
    #                #get_pk = _get_tag_pk,
    #            )
    #        
    #    }

    #can_delete = True

    list_template = 'admin/products.html'
    create_template = 'admin/product.html'
    edit_template = 'admin/product.html'

    #def get_query(self):
    #    return self.session.query(self.model).filter(self.model.is_available_on_web==True)

    # this method clear params include tags, parameters and images
    def _clear_product_params(self, product_id, param_name, data):
        values = ",".join([str(d.id) for d in data])
        if values:
            sql = 'DELETE FROM product_{0} WHERE product_id=:id AND {1}_id NOT IN (:values)'.format(param_name, param_name)
            t = text(sql, bindparams=[bindparam('id', type_=Integer, required=True),
                                     bindparam('values', type_=String, required=True)])
            self.session.execute(t, {"id": product_id, "values": values})

    def _update_product(self, form, model=None):
        if not model:
            model = Product(code=form.code.data)
            self.session.add(model)

        try:
            # normal fields
            for name, field in iteritems(form._fields):
                if name not in ('tags', 'parameters', 'images', 'code'):
                    field.populate_obj(model, name)

            # multiple choices fieldsfield.populate_obj
            # delete not checked tags
            #ProductTag.query.filter(ProductTag.product_id==model.id, ~ProductTag.tag_id.in_(tags)).delete(synchronize_session=False)
            self._clear_product_params(model.id, 'tag', form.tags.data)

            #product_tags = ProductTag.query.filter_by(product=model).all()
            for tag in form.tags.data:
                pt = ProductTag.query.get((model.id, tag.id))
                if not pt:
                    pt = ProductTag()
                    pt.product = model
                    pt.tag = tag
                    model.tags.append(pt)
                    self.session.add(pt)

            # parameters
            #params = [p.id for p in form.parameters.data]
            #ProductParameter.query.filter(ProductParameter.product_id==model.id, ~ProductParameter.parameter_id.in_(params)).delete(synchronize_session=False)
            self._clear_product_params(model.id, 'parameter', form.parameters.data)
            for param in form.parameters.data:
                pp = ProductParameter.query.get((model.id, param.id))
                if not pp:
                    pp = ProductParameter()
                    pp.product = model
                    pp.parameter = param
                    model.parameters.append(pp)
                    self.session.add(pp)

            # images
            #images = [i.id for i in form.images.data]
            self._clear_product_params(model.id, 'image', form.images.data)
            #ProductImage.query.filter(ProductImage.product_id==model.id, ~ProductImage.image_id.in_(images)).delete(synchronize_session=False)
            for image in form.images.data:
                pi = ProductImage.query.get((model.id, image.id))
                if not pi:
                    pi = ProductImage()
                    pi.product = model
                    pi.image = image
                    model.images.append(pi)
                    self.session.add(pi)

            self.session.commit()

            return True
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s', error=str(ex)), 'error')
                print('Failed to update record.')

            self.session.rollback()
            return False

    def create_model(self, form):
        return self._update_product(form)

    def update_model(self, form, model):
        return self._update_product(form, model)

    def delete_model(self, model):
        for t in model.tags:
            model.tags.remove(t)
            self.session.delete(t)
        for s in model.suppliers:
            model.suppliers.remove(s)
            self.session.delete(s)
        for p in model.parameters:
            model.parameters.remove(p)
            self.session.delete(p)
        #db.session.delete(model.tickets)
        for i in model.images:
            model.images.remove(i)
            self.session.delete(i)

        self.session.delete(model)
        self.session.commit();

        return True

class ImageView(BakeryView):
    @expose('/')
    def gallery(self):
        images = Image.query.all()
        category = GalleryCategory.query.all()

        return self.render('admin/gallery.html', data=images, category=category,
                            upload_action=url_for('.image_upload'))

    @expose('/image/<image_name>', methods=['GET', 'POST'])
    def image_detail(self, image_name):
        print(image_name)
        if request.method == 'POST':
            category_id = request.form.get('category')
            print('category id: ', category_id)
            if not category_id:
                abort(400) # bad request
            category = GalleryCategory.query.get_or_404(category_id)
            upload_name = request.form.get('name')
            title = request.form.get('title')
            description = request.form.get('description')
            image = Image.query.filter_by(name=image_name).first()
            image.upload_name = upload_name
            image.title = title
            image.description = description
            image.category = category
            #db.session.commit()
        else:
            image = Image.query.filter_by(name=image_name).first()

        categories = GalleryCategory.query.all()
        return self.render('admin/image.html', image=image, categories=categories)

    @expose('/image-upload', methods=['POST'])
    def image_upload(self):
        # do upload
        #images = None # uploaded images
        if request.method != 'POST':
            abort(405)

        files = request.files.getlist('upload-image')
        for f in files:
            filename = f.filename
            if not filename:
                abort(400)
            upload_name, name, ext = self.__generate_filename(filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], '.'.join([name, ext])))

            image = Image(upload_name=upload_name, name=name, directory=current_app.config['UPLOAD_FOLDER'], ext=ext)
            db.session.add(image)
            db.session.commit()

        return redirect(url_for('.gallery'))

    @expose('/image-delete', methods=['POST'])
    def image_delete(self):
        if request.method != 'POST':
            abort(405)

        #print(request.headers)
        #print(request.args)
        #print(request.form)
        name = request.form.get('name')
        if not name:
            abort(400)

        image = Image.query.filter_by(name=name).first()
        if image.products:
            message = {"errcode": 1, "errmsg": "Image was used by product"}
            return jsonify(message), 403

        try:
            # remove image from harddisk
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], '.'.join([name, image.ext]))
            os.remove(path)
        except Exception as e:
            print(e)

        # remove recode from database
        db.session.delete(image)
        db.session.commit()

        message = {"errcode": 0, "errmsg": "success"}
        return jsonify(message), 200

    def __generate_filename(self, filename):
        from time import time
        pos = filename.rfind('.')
        if pos > 0:
            upload_name = filename[:pos]
            ext = filename[pos+1:]
            return upload_name, str(time()), ext
        else:
            return filename, str(time()), ''

class SaleView(AdminIndexView):
    def _summary(self, begin_date, days=1):
        tickets = Ticket.query.filter(Ticket.pay_time >= begin_date, Ticket.pay_time < begin_date+timedelta(days=days))

        return self.render('admin/sale.summary.html', tickets=tickets)

    @expose('/')
    def index(self):
        d = datetime.today().date()
        return self._summary(d)

    @expose('/summary')
    def summary(self):
        d = datetime.strptime(summary_date, '%Y%m%d').date()
        return self._summary(d)

    def is_accessible(self):
        ua = login.current_user
        if not getattr(ua, 'is_staff', None):
            return False

        return ua.is_active() and ua.is_authenticated()

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))
#    list_template = 'admin/gallery.html'
#    edit_template = 'admin/image.html'
#
#    def _upload_image(self):
#        pass
