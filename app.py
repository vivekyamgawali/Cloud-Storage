from flask import Flask, render_template, url_for, request, session, redirect,make_response,jsonify,json
from flask_pymongo import PyMongo
from flask_jsglue import JSGlue
from werkzeug.utils import secure_filename
import bcrypt

app = Flask(__name__)
jsglue = JSGlue(app)

app.config['MONGO_DBNAME'] = 'Cloud_Storage'
app.config['MONGO_URI'] = 'mongodb+srv://vivek:vivek123@storage-r0mya.mongodb.net/Cloud_Storage'

mongo = PyMongo(app)

@app.route('/')
def index():
    if 'username' in session:
        return  redirect(url_for('my_drive'))
    return  redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users = mongo.db.cloud_users
        login_user = users.find_one({'name' : request.form['username']})
        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            else:
                return 'Invalid password combination'
        else:
            return 'Invalid username/password combination'
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.cloud_users
        existing_user = users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register.html')

@app.route('/my_drive', methods=['POST', 'GET'])
def my_drive():
    users = mongo.db.cloud_users
    existing_user = users.find_one({'name' : session['username']})
    uid = existing_user['_id']
    db_files = mongo.db.fs.files.find({'uid': uid}).sort("uploadDate", -1).limit(5)
    file_list = [ ]
    if db_files != None:
        for doc in db_files:
            file_list.append(doc)
    else:
        return render_template('my_drive.html', files= None)
    if request.method == 'POST':
        if 'abc' in request.files:
            nfiles = request.files.getlist('abc')
            for nfile in nfiles:
                mongo.save_file(nfile.filename, nfile, base='fs', content_type=None, uid=uid )
            return 'File Uploaded'
        else:
            uploaded_files = request.files.getlist("xyz")
            for files in uploaded_files:
                folder=files.filename.split('/')
                mongo.save_file(folder[1], files, base='fs', content_type=None, uid=uid, foldername=folder[0])
    return render_template('my_drive.html', files=file_list)

@app.route('/download/<file_name>', methods=['POST', 'GET'])
def download(file_name):
    grid_fs_file = mongo.db.fs.files.find_one({'filename': file_name})
    response = make_response(mongo.send_file(file_name))
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers["Content-Disposition"] = "attachment; filename={}".format(file_name)
    return response

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)