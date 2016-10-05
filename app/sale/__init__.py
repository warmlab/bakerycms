from flask import Blueprint

sale = Blueprint('sale', __name__)

from . import views, errors
#from ..models import Permission
#
#
#@sale.app_context_processor
#def inject_permissions():
#    return dict(Permission=Permission)
