from flask import Flask, render_template, url_for, request, session, redirect,make_response,jsonify
from flask_pymongo import PyMongo
from flask_restplus import Resource, Api, reqparse
from bson import json_util, ObjectId
import bcrypt
import werkzeug

app = Flask(__name__)
api = Api(app)

app.config['MONGO_DBNAME'] = 'Cloud_Storage'
app.config['MONGO_URI'] = 'mongodb+srv://vivek:vivek123@storage-r0mya.mongodb.net/Cloud_Storage'

mongo = PyMongo(app)

parser = reqparse.RequestParser()


class Registration(Resource):
    def post(self):
        parser.add_argument('username')
        parser.add_argument('password')
        data = parser.parse_args()
        users = mongo.db.cloud_users
        if users.find_one({'name' : data['username']}):
            return jsonify({'msg' : 'Username already exists'})
        else:
            hashpass = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name' : data['username'], 'password' : hashpass})
            session['username'] = data['username']
            return jsonify({'msg' : 'User Registered'}) 

class Login(Resource):
    def post(self):
        parser.add_argument('username')
        parser.add_argument('password')
        data = parser.parse_args()
        users = mongo.db.cloud_users
        login_user = users.find_one({'name' : data['username']})
        if login_user:
            if bcrypt.hashpw(data['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = data['username']
                return jsonify({'msg' : 'User loged in'})
            else:
                return jsonify({'msg' : 'Invalid password combination'})
        else:
            return jsonify({'msg' : 'Invalid username/password combination'})

class Storage(Resource):
    def get(self):
        users = mongo.db.cloud_users
        existing_user = users.find_one({'name' : session['username']})
        uid = existing_user['_id']
        db_files = mongo.db.fs.files.find({'uid': uid}).sort("uploadDate", -1).limit(5)
        file_list = [ ]
        if db_files != None:
            for doc in db_files:
                file_list.append(json_util.dumps(doc))
            return jsonify({'msg' : 'user loged in','files' : file_list})
        else:
            return jsonify({'msg' : 'user loged in','files' : None})

class File(Resource):
    def post(self):
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files', action='append')
        args = parser.parse_args()
        users = mongo.db.cloud_users
        existing_user = users.find_one({'name' : session['username']})
        uid = existing_user['_id']
        if args['file']:
            for files in args['file']:
                mongo.save_file(files.filename, files, base='fs', content_type=None, uid=uid )
            return jsonify({'msg' : 'file uploaded'})
        else:
            return jsonify({'msg' : 'Somthing went wrong'})

class Folder(Resource):
    def post(self):
        parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files',action='append')
        args = parser.parse_args()
        users = mongo.db.cloud_users
        existing_user = users.find_one({'name' : session['username']})
        uid = existing_user['_id']
        if args['file']:
            for files in args['file']:
                folder=files.filename.split('/')
                mongo.db.folders.insert({'foldername' : folder[0], 'uid' : uid})
                mongo.save_file(folder[1], files, base='fs', content_type=None, uid=uid, foldername=folder[0])
            return jsonify({'msg' : 'folder uploaded'})
        else:
            return jsonify({'msg' : 'Somthing went wrong'})


class Download(Resource):
    def get(self):
        parser.add_argument('filename')
        data = parser.parse_args()
        response = make_response(mongo.send_file(data['filename']))
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers["Content-Disposition"] = "attachment; filename={}".format(data['filename'])
        return response

api.add_resource(Registration, '/registration')
api.add_resource(Login, '/login')
api.add_resource(Storage, '/mydrive')
api.add_resource(Download, '/file_download')
api.add_resource(Folder, '/folder_upload')
api.add_resource(File, '/files_upload')

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)