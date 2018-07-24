from flask import Blueprint

api = Blueprint('api', __name__)

from . import product
from . import shop
from . import dragon
from . import errors

