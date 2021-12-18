from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import numpy as np
from skimage import transform
import keras
from skimage import io
import os


app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '1a2b3c4d5e'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'weedclassification'

# Intialize MySQL
mysql = MySQL(app)



BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH,'static/upload/')

model = keras.models.load_model("./static/models/weed_classifier.h5")

def load(filename):
   np_image = io.imread(filename) #Open the image
   np_image = np.array(np_image).astype('float32')/255 #Creates a numpy array as float and divides by 255.
   np_image = transform.resize(np_image, (150, 150, 3)) #Resize a 150x150 con 3 channels
   # We rescale it to(1, 150, 150, 3)
   #Since you trained your model on mini-batches, your input is a tensor of shape [batch_size, image_width, image_height, number_of_channels].
   np_image = np.expand_dims(np_image, axis=0) #Insert a new axis that will appear at the axis position in the expanded array shape.
   return np_image

classification={"broadweed":0,"grass":1,"soil":2, "soyabean":3}



# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE user_name = %s AND user_password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['user_id']
            session['username'] = account['user_name']
            # Redirect to home page
            return redirect(url_for('index'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg='')


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE user_name = %s', [username])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO user VALUES (NULL, %s, %s, %s)', (email, username, password))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)



@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        upload_file = request.files['image_name']
        filename = upload_file.filename
        print('The filename that has been uploaded =', filename)
        # know the extension of filename
        # all only .jpg, .png, .jpeg, PNG
        ext = filename.split('.')[-1]
        print('The extension of the filename =', ext)
        if ext.lower() in ['png', 'jpg', 'jpeg']:
            # saving the image
            file_path = os.path.join(UPLOAD_PATH, filename)
            upload_file.save(file_path)
            print('File saved sucessfully')

            # We take an image of the test
            image_to_predict = load(file_path)
            result = model.predict(image_to_predict)
            result = np.around(result, decimals=3)
            result = result * 100
            print(classification)
            print(result)


            return render_template('upload.html',fileupload=True,extension=False,data=result,image_filename=filename)


        else:
            print('Use only the extension with .jpg, .png, .jpeg')

            return render_template('upload.html',extension=True,fileupload=False)

    else:
        return render_template('upload.html',extension=False,fileupload=False)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return redirect(url_for('index'))
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.debug = True
    app.run()
