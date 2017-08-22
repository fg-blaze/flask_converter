import xml.etree.ElementTree as ET
import os
import logging
import io
from flask import Flask, request, redirect, url_for, flash, render_template,\
    send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'wpt'}

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        f = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if f.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f_path = os.path.join(app.config['UPLOAD_FOLDER'], filename+'.kml')
            f.save(f_path)
            logger.info('File path: {}'.format(f_path))
            convert_ozi_to_maverick(f_path, f_path)
            return send_from_directory(
                directory=app.config['UPLOAD_FOLDER'],
                filename=filename + '.kml'
            )
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/')
def show_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('files.html', files=files)


def convert_ozi_to_maverick(in_path, out_path):
    # ozi_path = '/home/vshyp/Downloads/Troeborye 2017.wpt'
    # out_path = '/home/vshyp/Downloads/out.kml'

    with io.open(in_path, encoding='utf-8', errors='ignore') as f:
        points = f.readlines()

    header = """<?xml version="1.0" encoding="UTF-8"?>"""
    kml = ET.Element('kml', attrib={'xmlns': "http://earth.google.com/kml/2.2"})
    document = ET.SubElement(kml, 'Document')
    list_name = ET.SubElement(document, 'name')
    list_name.text = 'Points.kml'
    folder = ET.SubElement(document, 'Folder',)
    is_open = ET.SubElement(folder, 'open')
    is_open.text = '1'
    mav_name = ET.SubElement(folder, 'name')
    mav_name.text = 'Maverick'

    for point in points[4:]:
        point_name, N, E, = point.split(',')[1:4]
        placemark = ET.SubElement(folder, 'Placemark')
        name = ET.SubElement(placemark, 'name')
        desc = ET.SubElement(placemark, 'description')
        point = ET.SubElement(placemark, 'Point')
        coords = ET.SubElement(point, 'coordinates')
        name.text = point_name
        desc.text = 'Manual location'
        coords.text = '{},{}'.format(E.strip(), N.strip())

    res_xml = '{}{}'.format(header, ET.tostring(kml))

    with io.open(out_path, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(res_xml)
