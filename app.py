import sys

from flask import Flask, request, flash, redirect, render_template_string
from werkzeug.utils import secure_filename
from yaml import safe_load
import psycopg2
import psycopg2.errorcodes

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
            <button onclick="window.location.href = '/createperson'">Create New Person</button>
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

@app.route('/createperson', methods=['GET', 'POST'])
def create_person():
    cur = conn.cursor()
    institutes = {}
    departments = {}
    labs = {}

    cur.execute('SELECT id, name, type from organizations')
    for row in cur.fetchall():
        if row[2] == 'institute':
            institutes[row[1]] = row[0]
        elif row[2] == 'department':
            departments[row[1]] = row[0]
        elif row[2] == 'lab':
            labs[row[1]] = row[0]
        else:
            pass
            # what do we do

    cur.close()
    if request.method == 'POST':
        cur = conn.cursor()
        try:
            first_name = request.form['first_name'].strip()
            last_name = request.form['last_name'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            institute = request.form['institute'].strip()
            department = request.form['department'].strip()
            lab = request.form['lab'].strip()

            if first_name is '' or last_name is '':
                flash('First and last name are required')
                return redirect(request.url)

            cur.execute('INSERT INTO people (display_name, email, phone) VALUES (%s, %s, %s) RETURNING id', (first_name + ' ' + last_name, email, phone))
            id = cur.fetchone()[0]
            cur.execute('INSERT INTO names (person_id, first_name, last_name) VALUES (%s, %s, %s)', (id, first_name, last_name))

            if institute is not '':
                if institute in institutes:
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (institutes[institute], id))
                else:
                    cur.execute('INSERT INTO organizations (name, type) VALUES (%s, %s) RETURNING id', (institute, 'institute'))
                    org_id = cur.fetchone()[0]
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (org_id, id))

            if department is not '':
                if department in departments:
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (departments[department], id))
                else:
                    cur.execute('INSERT INTO organizations (name, type) VALUES (%s, %s) RETURNING id', (department, 'department'))
                    org_id = cur.fetchone()[0]
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (org_id, id))
            
            if lab is not '':
                if lab in labs:
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (labs[lab], id))
                else:
                    cur.execute('INSERT INTO organizations (name, type) VALUES (%s, %s) RETURNING id', (lab, 'lab'))
                    org_id = cur.fetchone()[0]
                    cur.execute('INSERT INTO associations (organization_id, person_id) VALUES (%s, %s)', (org_id, id))

            conn.commit()
            flash('Person created successfully')
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if e.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
                flash('First and Last name pair must be unique')
            else:
                print(e)
                flash('Other integrity error')
        except Exception as e:
            print(e)
            conn.rollback()
            flash('Error creating a new person')
        finally:
            cur.close()
        return redirect(request.url)
    
    return render_template_string('''
    <!doctype html>
    <head>
        <title>Create a new Person</title>
    </head>
    <body>
        <h1>Create a new Person</h1>
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
            <input type=text name=first_name required>
            
            <label>Last Name</label>
            <input type=text name=last_name required>
            
            <label>Email</label>
            <input type=email name=email>

            <label>Phone Number</label>
            <input type=tel name=phone>

            <label>Institute</label>
            <input list=institutes name=institute>
            <datalist id=institutes>
                {% for inst in instituteList %}
                    <option value="{{inst}}">
                {% endfor %}
            </datalist>

            <label>Department</label>
            <input list=departments name=department>
            <datalist id=departments>
                {% for dept in departmentList %}
                    <option value="{{dept}}">
                {% endfor %}
            </datalist>

            <label>Labs</label>
            <input list=labs name=lab>
            <datalist id=labs>
                {% for labItem in labList %}
                    <option value="{{labItem}}">
                {% endfor %}
            </datalist>
            
            <input type=submit value=Create>
        </form>
    </body>
    ''', instituteList=institutes.keys(), departmentList=departments.keys(), labList=labs.keys())
