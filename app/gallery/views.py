import os

from datetime import datetime
from decimal import Decimal

from flask import render_template
from flask import current_app, request
from flask import send_from_directory

from werkzeug.utils import secure_filename

from . import gallery
from .. import db

from ..models import Image

def __generate_filename(filename):
    from time import time
    pos = filename.rfind('.')
    if pos > 0:
        upload_name = filename[:pos]
        ext = filename[pos+1:]
        return upload_name, str(time()), ext
    else:
        return filename, str(time()), ''

@gallery.route('/images', methods=['GET'])
def image_list():
    images = Image.query.all()
    return render_template('gallery/images.html', images=images)

@gallery.route('/image/<name>', methods=['GET', 'POST'])
def image_detail(name):
    if request.method == 'POST':
        upload_name = request.form.get('inputname')
        title = request.form.get('inputtitle')
        description = request.form.get('inputdesc')
        image = Image.query.filter_by(name=name).first()
        image.upload_name = upload_name
        image.title = title
        image.description = description
    else:
        image = Image.query.filter_by(name=name).first()
    return render_template('gallery/image.html', image=image)

@gallery.route('/image/upload', methods=['GET', 'POST'])
def image_upload():
    # do upload
    #images = None # uploaded images
    if request.method == 'POST':
        files = request.files.getlist('upload-image')
        for f in files:
            filename = f.filename
            upload_name, name, ext = __generate_filename(filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], '.'.join([name, ext])))

            image = Image(upload_name, name, current_app.config['UPLOAD_FOLDER'], ext)
            db.session.add(image)
            db.session.commit()

    return render_template('gallery/image-uploader.html')

@gallery.route('/media/<filename>')
def media_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
