from flask import Flask, render_template_string, render_template, Response, request, redirect, url_for, make_response
import pymongo
import random
import string

WEBSITE_URL = "localhost"
app = Flask(__name__)
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client["SE2_Friend_Finder"]
user_account_db = my_db["user_accounts"]
user_profile_db = my_db["user_profiles"]


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
        return user_profile('blank', 'blank', 'blank', 'blank', 'blank', 'blank', [])


def verify_credentials(username, password):
    verified = False
    count = 0
    query = {"username": username, "password": password}
    mydoc = user_account_db.find(query)
    for x in mydoc:
        count+=1

    if count > 0:
        verified = True

    return verified

@app.route('/')
def index():
    return render_template('views/index.html')


@app.route('/create_profile', methods=['POST'])
def create_profile(username, name, age, major, year, biography, interests):
    profile_dict = {"username": username, "name": name, "age": age, "major": major, "year": year, "biography": biography, "interests": interests}
    user_profile_db.insert_one(profile_dict)



@app.route('/create_account', methods=['POST'])
def create():
    try:
        username = request.form['username']
        password = request.form['password']
        if not find_account(username):
            account_dict = {"username": username, "password": password}
            user_account_db.insert_one(account_dict)
            return render_template_string("account created")
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
        resp = make_response(render_template('views/profile.html', user_profile=find_user_profile(username)))
        resp.set_cookie('userID', username)
        return resp

    else:
        return render_template('views/error.html', err='User/password combo entered does not exist.')

@app.route('/profile/<username>')
def get_user(username):
    user = find_user_profile(username)
    if user.username == 'blank':
        return render_template('views/error.html', err='User not found.')
    else:
        return render_template('views/profile.html', user_profile=user)

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')



if __name__ == '__main__':
    app.run(port=80, debug=True)
