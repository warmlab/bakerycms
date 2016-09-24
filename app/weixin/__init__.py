from flask import Blueprint

weixin = Blueprint('weixin', __name__)

from . import views, errors
#from ..models import Permission
#
#
#@shop.app_context_processor
#def inject_permissions():
#    return dict(Permission=Permission)
