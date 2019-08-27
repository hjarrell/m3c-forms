import sys

from flask import Flask, request, flash, redirect, render_template_string
from werkzeug.utils import secure_filename
from yaml import safe_load
import psycopg2

CONFIG_FILE = 'config.yml'

config_map = None
picture_path = ''
secret_key = ''
db_host = ''
db_database = ''
db_user = ''
db_password = ''

with open(CONFIG_FILE, 'r') as f:
    config_map = safe_load(f)
    picture_path = config_map['picturepath']
    secret_key = config_map['secret']
    db_host = config_map['dbhost']
    db_database = config_map['dbdatabase']
    db_user = config_map['dbuser']
    db_password = config_map['dbpassword']

try:
    conn = psycopg2.connect(database=db_database, user=db_user, password=db_password, host=db_host)
except:
    print('Cannot connect to the database')
    sys.exit(-1)

app = Flask(__name__)
app.secret_key = secret_key

@app.route('/')
def main_menu():
    return '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>M3C Admin Form</title>
        </head>
        <body>
            <h1>M3C Admin Form</h1>
            <button onclick="window.location.href = '/uploadimage'">Upload Profile Picture</button>
        </body>
    </html>
    '''

@app.route('/uploadimage', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            picture_file = request.files['picture']
            extension = picture_file.filename.split('.')[-1]
            picture_file.save('{}/'.format(picture_path) + secure_filename('{}_{}.{}'.format(last_name, first_name, extension)))
            flash('Completed save sucessfully')
            return redirect(request.url)
        except Exception:
            flash('Error uploading file')
            return redirect(request.url)
    
    return render_template_string('''
    <!doctype html>
    <head>
        <title>Upload a new picture</title>
    </head>
    <body>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    {{ message }}
                    <br/>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method=post enctype=multipart/form-data>
            <label>First Name</label>
            <input type=text name=first_name>
            <label>Last Name</label>
            <input type=text name=last_name>
            <input type=file name=picture>
            <input type=submit value=Upload>
        </form>
    </body>
    ''')
