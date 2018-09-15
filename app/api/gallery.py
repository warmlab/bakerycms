import os
import hashlib

from time import time

from flask import json, jsonify, abort
from flask import request, current_app

from . import api

from ..models import db
from ..models import Shoppoint
from ..models import Image, GalleryCategory


def generate_filename(filename):
    pos = filename.rfind('.')
    if pos > 0:
        upload_name = filename[:pos]
        ext = filename[pos+1:]
        return upload_name, str(time()), ext
    else:
        return filename, str(time()), ''

def generate_hash_value(file_storage):
    md5 = hashlib.md5()
    md5.update(file_storage.read())
    file_storage.seek(0)

    return md5.hexdigest()

@api.route('/<shopname>/gallery', methods=['POST'])
def image_new(shopname):
    sp = Shoppoint.query.filter_by(code=shopname).first_or_404()
    added = False
    images = []
    category = GalleryCategory.query.filter_by(name=request.form['type'], shoppoint_id=sp.id).first()
    if not category:
        category = GalleryCategory()
        category.name = request.form['type']
        category.description = 'added by dragon mini app'
        db.session.add(category)

    for f in request.files.getlist('upload-files'):
        hash_value = generate_hash_value(f)
        image = Image.query.filter_by(hash_value=hash_value, shoppoint_id=sp.id).first()
        if image:
            images.append(image)
            continue

        upload_name, name, ext = generate_filename(f.filename)
        print(current_app.config['UPLOAD_FOLDER'], name, ext)
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], '.'.join([name, ext])))
        image = Image(name=name, upload_name=name, directory=current_app.config['UPLOAD_FOLDER'], ext='jpg')
        image.hash_value = hash_value
        image.category = category
        image.Shoppoint = sp
        images.append(image)

        db.session.add(image)
        added = True

    if added:
        db.session.commit()

    array = []
    for i in images:
        item = i.to_json()
        item['index'] = int(request.form.get('index'))
        array.append(item)

    return jsonify(array), 201
