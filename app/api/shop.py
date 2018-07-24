from flask import json
from flask import request
from flask.json import jsonify

from . import api

from ..models import DragonAddress

@api.route('/<shop>/info', methods=['GET'])
def shopinfo(shop):
    print(shop)
    d = {"name": "小麦芬烘焙工作室"}
    return jsonify(d)
