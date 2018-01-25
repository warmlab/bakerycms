#from wtforms import Form
from wtforms.widgets import TextInput, TextArea, CheckboxInput, ListWidget
from wtforms import StringField, TextField, TextAreaField, PasswordField, BooleanField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField

from flask_wtf import RecaptchaField

from flask_admin.form import BaseForm

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class ProductForm(BaseForm):
    description = CKTextAreaWidget()
    name = TextField('产品名称', validators=[DataRequired()])
    english_name = TextField('英文名称', 
            validators=[DataRequired(message='英文名称不能为空'),],
        widget=TextInput(),
        render_kw={'class': 'ui input'}
        )
    #tags = TextField('标签', validators=[DataRequired()])
    tags = SelectMultipleField('标签', choices = [(1, 'a'),(2, 'b')])
    #tags.multiple = 1
    #tags.data = 1
    #recaptcha = RecaptchaField()

class ImageForm(BaseForm):
    pass
