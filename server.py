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
friend_db = my_db["friend_relationships"]
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


def verify_credentials(username, password):
    verified = False
    count = 0
    query = {"username": username}
    mydoc = user_account_db.find(query)
    for x in mydoc:
        if password == f.decrypt(x['password']).decode():
            verified = True

    return verified

def get_incoming(username):
    accs = []
    query = {"username2": username, "status": 1}
    mydoc = friend_db.find(query)
    for x in mydoc:
        accs.append(x['username1'])

    return accs


def get_outgoing(username):
    accs = []
    query = {"username1": username, "status": 1}
    mydoc = friend_db.find(query)
    for x in mydoc:
        accs.append(x['username2'])

    return accs

def get_friends(username):
    accs = []
    query = {"username1": username, "status": 2}
    mydoc = friend_db.find(query)
    for x in mydoc:
        accs.append(x['username2'])

    return accs

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


def accept_friend_request(username1, username2):
    myquery = {"username1": username1, "username2": username2}
    profile_dict = { "$set": {"status": 2}}
    friend_dict = {"username1": username2, "username2": username1, "status": 2}
    friend_db.insert_one(friend_dict)
    friend_db.update_one(myquery, profile_dict)


def cancel_friend_request(username1, username2):
    myquery = {"username1": username1, "username2": username2}
    myquery2 = {"username2": username1, "username1": username2}
    friend_db.delete_one(myquery)
    friend_db.delete_one(myquery2)


def check_friendship(username1, username2):
    status = 0
    query = {"username1": username1, "username2": username2}
    mydoc = friend_db.find(query)
    for x in mydoc:
        if x:
            status = x['status']

    return status

def create_a_friendship(username1, username2):
    try:
        friend_dict = {"username1": username1, "username2": username2, "status": 1}
        friend_db.insert_one(friend_dict)
        return True

    except:
        return False



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


@app.route('/search', methods=['POST'])
def search():
    query = request.form['searchquery']
    # find the query if its in bio/name/interests of all users

    return render_template('views/searchresults.html', results=results)


@app.route('/friends')
def friends():
    username = request.cookies.get('userID')
    if username: authed = True
    incoming = get_incoming(username)
    outgoing = get_outgoing(username)
    friends = get_friends(username)

    return render_template('views/friends.html', authed=authed, auth=username, friends=friends, outgoing=outgoing, incoming=incoming, leni=len(incoming), leno=len(outgoing), lenf=len(friends))


@app.route('/create_friendship', methods=['POST'])
def create_friendship():
    users = request.args.get('users').split(' ')
    if create_a_friendship(users[0], users[1]):
        return redirect(request.referrer)

    else:
        return render_template('views/error.html', err='Could not add friend.')


@app.route('/confirm_friendship', methods=['POST'])
def confirm():
    users = request.args.get('users').split(' ')
    if check_friendship(users[0], users[1]) == 1:
        accept_friend_request(users[0], users[1])
        return redirect(request.referrer)

    else:
        return render_template('views/error.html', err='Can not confirm a friendship that doesn\'t exist.')


@app.route('/cancel_friendship', methods=['POST'])
def cancel_friend_ship():
    users = request.args.get('users').split(' ')
    if (check_friendship(users[0], users[1]) != 0) or (check_friendship(users[1], users[0]) != 0):
        cancel_friend_request(users[0], users[1])
        return redirect(request.referrer)

    else:
        return render_template('views/error.html', err='Can not cancel a friendship that doesn\'t exist.')


@app.route('/all-profiles')
def get_all():
    username = request.cookies.get('userID')
    user_profile_list = []
    cursor = user_profile_db
    for x in cursor.find():
        pro = user_profile(x['username'], x['name'], x['age'], x['major'], x['year'], x['biography'], x['interests'])
        user_profile_list.append(pro)


    if username:
        return render_template('views/allprofiles.html', check_friendship=check_friendship, authed=True, auth=username, user_profile_list=user_profile_list)

    else:
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
        username = request.form['username'].replace(' ', '')
        if len(username) > 1:
            password = f.encrypt(request.form['password'].encode())
            if not find_account(username):
                account_dict = {"username": username, "password": password}
                user_account_db.insert_one(account_dict)
                resp = make_response(redirect(f'/profile/{username}'))
                resp.set_cookie('userID', username)
                return resp

            else:
                return render_template('views/error.html', err='Username already taken.')

        else:
            return render_template('views/error.html', err='Please enter a non-spaced username.')

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


@app.route('/setup-profile')
def setup_profile():
    try:
        auth = request.cookies.get('userID')
        if auth:
            return render_template('views/createprofile.html', authed=True, username=auth)
    except Exception as profile_err:
        print(profile_err)
        return render_template('views/error.html', err='Please log in to edit profile.')


@app.route('/profile/<username>')
def get_user(username):
    setup = False
    authedself = False
    authed = False
    auth = request.cookies.get('userID')
    if auth == username:
        authedself = True

    if auth:
        authed = True

    user = find_user_profile(username)

    if user:
        return render_template('views/profile.html', check_friendship=check_friendship, auth=auth, authedself=authedself , user_profile=user, authed=authed)
    else:
        if authed:
            return redirect('/setup-profile')
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
    if auth:
        user = find_user_profile(auth)
        interests = ', '.join(user.interests)
        if user:
            return render_template('views/editprofile.html', user_profile=user, interests=interests, authed=True)
        else:
            if authed:
                return redirect('/setup-profile')

    else:
        return render_template('views/error.html', err='Please log in to edit profile.')



@app.route('/edit-profile-layout', methods=['POST'])
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
