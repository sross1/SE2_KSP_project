from flask import Flask, render_template_string, render_template, Response, request, redirect, url_for, make_response
from cryptography.fernet import Fernet
import pymongo
import random
import string

WEBSITE_URL = "localhost"
app = Flask(__name__)
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client["SE2_Friend_Finder"]
user_account_db = my_db["user_accounts"]
user_profile_db = my_db["user_profiles"]
key = open('encrypt.key', 'rb').read()
f = Fernet(key)

class user_account:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class user_profile:
    def __init__(self, username, name, age, major, year, biography, interests):
        self.username = username
        self.name = name
        self.age = age
        self.major = major
        self.year = year
        self.biography = biography
        self.interests = interests


def find_account(username):
    found = False
    count = 0
    query = {"username": username}
    mydoc = user_account_db.find(query)
    for x in mydoc:
        count+=1

    if count > 0:
        found = True

    return found

def find_user_profile(username):
    found = False
    accs = []
    query = {"username": username}
    mydoc = user_profile_db.find(query)
    for x in mydoc:
        found = True
        pro = user_profile(x['username'], x['name'], x['age'], x['major'], x['year'], x['biography'], x['interests'])
        accs.append(pro)

    if found:
        return accs[0]

    else:
        return None


def verify_credentials(username, password):
    verified = False
    count = 0
    query = {"username": username}
    mydoc = user_account_db.find(query)
    for x in mydoc:
        if  password == f.decrypt(x['password']).decode():
            verified = True

    return verified

@app.route('/')
def index():
    try:
        username = request.cookies.get('userID')
        if username:
            return render_template('views/index.html', authed=True, username=username)

        else:
            return render_template('views/index.html', authed=False, username='')
    except:
        return render_template('views/index.html', authed=False, username='')

@app.route('/all-profiles')
def get_all():
    try:
        username = request.cookies.get('userID')
        user_profile_list = []
        cursor = user_profile_db
        for x in cursor.find():
            pro = user_profile(x['username'], x['name'], x['age'], x['major'], x['year'], x['biography'], x['interests'])
            user_profile_list.append(pro)


        if username:
            return render_template('views/allprofiles.html', authed=True, username=username, user_profile_list=user_profile_list)

        else:
            return render_template('views/allprofiles.html', authed=False, user_profile_list=user_profile_list)

    except:
        return render_template('views/allprofiles.html', authed=False, user_profile_list=user_profile_list)


@app.route('/create_profile', methods=['POST'])
def create_profile():
    try:
        username = request.cookies.get('userID')
        if not find_user_profile(username):
            name = request.form['realname']
            age = request.form['age']
            major = request.form['major']
            year = request.form['year']
            biography = request.form['biography']
            interests = [i.strip() for i in request.form['interests'].split(',')]
            profile_dict = {"username": username, "name": name, "age": age, "major": major, "year": year, "biography": biography, "interests": interests}
            user_profile_db.insert_one(profile_dict)
            return redirect(f'/profile/{username}')

        else:
            return render_template('views/error.html', err='Profile has already been set up. Please edit any mistakes.')

    except Exception as err:
        return render_template('views/error.html', err=err)



@app.route('/create_account', methods=['POST'])
def create():
    try:
        username = request.form['username']
        password = f.encrypt(request.form['password'].encode())
        if not find_account(username):
            account_dict = {"username": username, "password": password}
            user_account_db.insert_one(account_dict)
            resp = make_response(redirect(f'/profile/{username}'))
            resp.set_cookie('userID', username)
            return resp
        else:
            return render_template('views/error.html', err='Username already taken.')

    except Exception as error:
        print(f'ERROR: {str(error)}')


@app.route('/register', methods=['GET'])
def register():
    return render_template('views/register.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if verify_credentials(username, password):
        resp = make_response(redirect(f'/profile/{username}'))
        resp.set_cookie('userID', username)
        return resp

    else:
        return render_template('views/error.html', err='User/password combo entered does not exist.')


@app.route('/setup_profile')
def setup_profile():
    try:
        auth = request.cookies.get('userID')
        if auth:
            return render_template('views/createprofile.html', authed=True, username=auth)
    except Exception:
        return render_template('views/error.html', err='Please log in to edit profile.')


@app.route('/profile/<username>')
def get_user(username):
    setup = False
    authed = False
    auth = request.cookies.get('userID')
    if auth == username:
        authed = True

    user = find_user_profile(username)

    if user:
        return render_template('views/profile.html', user_profile=user, authed=authed)
    else:
        if authed:
            return redirect('/setup_profile')
        else:
            return render_template('views/error.html', err='Profile does not exist.')

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('userID', '', expires=0)
    return resp


@app.route('/edit_profile')
def edit_profile():
    auth = request.cookies.get('userID')
    user = find_user_profile(auth)
    interests = ', '.join(user.interests)
    if user:
        return render_template('views/editprofile.html', user_profile=user, interests=interests, authed=True)
    else:
        if authed:
            return redirect('/setup_profile')



@app.route('/edit_profile_layout', methods=['POST'])
def edit_profile_layout():
    auth = request.cookies.get('userID')
    user = find_user_profile(auth)
    myquery = { "username": auth }
    name = request.form['realname']
    age = request.form['age']
    major = request.form['major']
    year = request.form['year']
    biography = request.form['biography']
    interests = [i.strip() for i in request.form['interests'].split(',')]
    profile_dict = { "$set": {"name": name, "age": age, "major": major, "year": year, "biography": biography, "interests": interests}}
    user_profile_db.update_one(myquery, profile_dict)
    return redirect(f'/profile/{auth}')


@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')


if __name__ == '__main__':
    app.run(port=80, debug=True)
