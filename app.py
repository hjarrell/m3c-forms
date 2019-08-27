from flask import Flask, request, flash, redirect, render_template_string
from werkzeug.utils import secure_filename
from yaml import safe_load

CONFIG_FILE = 'config.yml'

config_map = None
picture_path = ''
secret_key = ''

with open(CONFIG_FILE, 'r') as f:
    config_map = safe_load(f)
    picture_path = config_map['picturepath']
    secret_key = config_map['secret']

app = Flask(__name__)
app.secret_key = secret_key

@app.route('/')
def main_menu():
    return ''

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
        except Exception as e:
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

app