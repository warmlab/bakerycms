from flask import Blueprint

gallery = Blueprint('gallery', __name__)

from . import views, errors
#from ..models import Permission
#
#
#@product.app_context_processor
#def inject_permissions():
#    return dict(Permission=Permission)