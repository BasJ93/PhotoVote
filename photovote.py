#!/usr/bin/env python

# -*- coding: utf-8 -*-
#"""
#Flask code adapted from: https://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972
#Created on Wed 14-02-2018
#
#@author: Bas Janssen
#"""

from flask import Flask, render_template, request, session, Markup, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
from datetime import timedelta
import getpass


app = Flask(__name__)
app.secret_key = 'This is a really secret key for this app'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes = 360)

@app.route('/')
def index():
    if session.get('uuid'):
        pass
    else:
        session['uuid'] = uuid.uuid4()
    try:
        _photographers = conn.execute('''select ID, NAME from Photographers order by cast(NAME as int) asc;''') #A really dirty hack, but names are currently set as just integers. Perhaps change the table with a display name collumn.
    except sqlite3.Error as e:
        return render_template('error.html', error = str(e.args[0]))
    _overview = "<table class='table table-hover'><tr><th>Photographers</th></tr>"
    _script = "<script>$(document).ready( function() {"
    for row in _photographers:
        try:
            _rating = conn.execute('''select RATING from Ratings where PHOTOGRAPHER={_Photographer} and DAY=date('now') and USER='{_User}';'''.format(_Photographer=row[0], _User=session.get('uuid')))
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        _currentRating = 0
        row2 = _rating.fetchone()
        if row2 is None:
            pass
        else:
            _currentRating = row2[0] or 0
        _overview = _overview + "<tr><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr>".format(_photographer = row[0], _name = row[1])
        _script = _script + "$('{_photographer}').starRating({{useFullStars: true, starSize: 25, initialRating: {_rating}, disableAfterRate: false, callback: function(currentRating, $el){{$.post('addRating', {{'id': $el[0].id, 'rating': currentRating}});}}}});".format(_photographer = ".photo-rating-" + str(row[0]), _rating = _currentRating)
    _overview = _overview + "</table>"
    _script = _script + "});</script>"
    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'><span class='navbar-brand'>Photo Vote</span><button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button><div class='collapse navbar-collapse' id='collapsingNavbar'><ul class='navbar-nav ml-auto'><li class='nav-item'><a class='nav-link active' href='/login'>Login</a></li></ul></div></nav>"
    return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), script=Markup(_script))

@app.route('/overview')
def overview():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = conn.execute("select ID from Admin where NAME='{_Username}' and UUID='{_uuid}';".format(_Username = session.get('user'), _uuid = session.get('uuid')))
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins.fetchone() is None:
                return redirect('/')
            else:
                try:
                    _photographers = conn.execute('''select Photographers.ID, NAME, avg(RATING), sum(RATING), COUNT(RATING) from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') group by Photographers.ID order by sum(RATING) desc;''')
                except sqlite3.Error as e:
                    return render_template('error.html', error = str(e.args[0]))
                _overview = "<div class='table-responsive'><table class='table table-hover'><thead><tr><th>Photographer</th><th>Votes</th><th>Total score</th><th>Average score</th></tr></thead>"
                _script = "<script>$(document).ready( function() {"
                for row in _photographers:
                    _overview = _overview + "<tbody><tr class='clickable' data-toggle='collapse' data-target='#options-{_photographer}' aria-expanded='false' aria-controls='options-{_photographer}'><td>{_name}</td><td>{_votes}</td><td>{_TotalScore}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr></tbody><tbody id='options-{_photographer}' class='collapse'><tr><td colspan='2'><button type='button' class='btn btn-warning' id='btn-rename-{_photographer}'>Rename</button></td><td colspan='2'><button type='button' class='btn btn-danger' id='btn-remove-{_photographer}'>Remove</button></td></tr></tbody>".format(_photographer = row[0], _name = row[1], _TotalScore = row[3] or 0, _votes = row[4] or 0)
                    _script = _script + "$('{_photographer}').starRating({{starSize: 25, readOnly: true, initialRating: {_rating}}});".format(_photographer = ".photo-rating-" + str(row[0]), _rating = row[2] or 0)
                _overview = _overview + "</table></div>"
                _script = _script + "$('.btn-danger').click(function(event){$.post('removePhotographer', {'id': $(event.target).attr('id')});});"
                _script = _script + "});</script>"
                _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'><a class='navbar-brand' href='/'>Photo Vote</a><button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button><div class='collapse navbar-collapse' id='collapsingNavbar'><ul class='navbar-nav ml-auto'><li class='nav-item'><a class='nav-link active' href='/logout'>Logout</a></li><li class='nav-item'><a class='nav-link' href='/add_photographer'>Add Photographer</a></li><li class='nav-item'><a class='nav-link' href='/add_admin'>Add Admin</a></li></ul></div></nav>"
                return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), script=Markup(_script))
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/addRating", methods=['POST'])
def addRating():
    if session.get('uuid'):    
        try:
            conn.cursor().execute("insert or replace into Ratings (ID, RATING, USER, PHOTOGRAPHER, DAY) values ((select ID from Ratings where USER = '{_User}' and PHOTOGRAPHER = '{_Photographer}' and DAY=date('now')), '{_Rating}', '{_User}', '{_Photographer}', (date('now')));".format(_Photographer=request.form['id'], _Rating=request.form['rating'], _User=session.get('uuid')))
            conn.commit()
        except sqlite3.Error as e:
            print e.args[0]
            return render_template('error.html', error = str(e.args[0]))
        return "ok"
    else:
        return "invalid"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            _username = request.form['inputUsername']
            _password = request.form['inputPassword']
        except Exception as e:
            return render_template('error.html', error = str(e))        
        try:
            _pw_hashes = conn.execute("select PASSWORDHASH, UUID from Admin where NAME='{_user}';".format(_user = _username))
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        for _pw_hash in _pw_hashes:
            if _pw_hash is None:
                return redirect('/login')
            else:
                pw_hash = _pw_hash[0]
                uuid = _pw_hash[1]
                if check_password_hash(pw_hash, _password):
                    session['user'] = _username
                    session['uuid'] = uuid
                    return redirect('/overview')
                else:
                    return render_template('error.html',error = 'Invalid password.')
    
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = conn.execute("select ID from Admin where NAME='{_Username}' and UUID='{_uuid}';".format(_Username = session.get('user'), _uuid = session.get('uuid')))
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins.fetchone() is None:
                return render_template("login.html", path=Markup("login"), action=Markup("Login"))
            else:
                return redirect('/overview')
        else:
            return render_template("login.html", path=Markup("login"), action=Markup("Login"))
    else:
        return render_template("login.html", path=Markup("login"), action=Markup("Login"))
    
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route("/add_photographer", methods=['GET', 'POST'])
def add_photographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = conn.execute("select ID from Admin where NAME='{_Username}' and UUID='{_uuid}';".format(_Username = session.get('user'), _uuid = session.get('uuid')))
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins.fetchone() is None:
                return redirect('/')
            else:
                if request.method == 'POST':
                    try:
                        photographer = request.form['inputPhotographer']
                    except Exception as e:
                        return render_template('error.html', error = str(e))
                    try:
                        conn.execute("insert into Photographers (NAME) values ('{_photographer}');".format(_photographer = photographer))
                        conn.commit()
                    except sqlite3.Error as e:
                        return render_template('error.html', error = str(e.args[0]))
                    return redirect('/overview')
                    
                return render_template('add_photographer.html')
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/removePhotographer", methods=['POST'])
def removePhotographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = conn.execute("select ID from Admin where NAME='{_Username}' and UUID='{_uuid}';".format(_Username = session.get('user'), _uuid = session.get('uuid')))
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins.fetchone() is None:
                return "invalid"
            else:
                    try:
                        data = request.form['id'].split("-")
                        photographer = data[2]
                    except Exception as e:
                        print (e)
                        return "invalid"
                    try:
                        conn.execute("delete from Ratings where PHOTOGRAPHER='{_photographer}';".format(_photographer = photographer))
                        conn.commit()
                        conn.execute("delete from Photographers where ID='{_photographer}';".format(_photographer = photographer))
                        conn.commit()
                    except sqlite3.Error as e:
                        print (e)
                        return "invalid"
                    return "ok"
        else:
            return "invalid"

@app.route("/add_admin", methods=['GET', 'POST'])
def add_admin():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = conn.execute("select ID from Admin where NAME='{_Username}' and UUID='{_uuid}';".format(_Username = session.get('user'), _uuid = session.get('uuid')))
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins.fetchone() is None:
                return redirect('/')
            else:
                if request.method == 'POST':
                    try:
                        _username = request.form['inputUsername']
                        _password = request.form['inputPassword']
                    except Exception as e:
                        return render_template('error.html', error = str(e))
                    try:
                        conn.execute("insert into Admin (UUID, NAME, PASSWORDHASH) values ('{_UUID}', '{_Name}', '{_PWHash}');".format(_UUID = uuid.uuid4(), _Name = _username, _PWHash = generate_password_hash(_password)))
                        conn.commit()
                    except sqlite3.Error as e:
                        return render_template('error.html', error = str(e.args[0]))
                    return redirect('/overview')
                    
                return render_template("login.html", path=Markup("add_admin"), action=Markup("Add Admin"))
        else:
            return redirect('/')
    else:
        return redirect('/')


if __name__=="__main__":
    conn = sqlite3.connect('photovote.db')
    conn.execute('''PRAGMA foreign_keys = ON;''')
    conn.execute('''create table if not exists Admin(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, UUID TEXT, NAME TEXT, PASSWORDHASH TEXT);''') #The password must be hashed, plaintext can not be used.
    conn.execute('''create table if not exists Photographers(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, NAME TEXT NOT NULL);''')
    conn.execute('''create table if not exists Ratings(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, RATING REAL NOT NULL, DAY TEXT NOT NULL, USER TEXT NOT NULL, PHOTOGRAPHER INT NOT NULL, FOREIGN KEY(PHOTOGRAPHER) REFERENCES PHOTOGRAPHERS(ID));''')
    
    try:
        _admins = conn.execute("select ID from Admin;")
    except sqlite3.Error as e:
        print (str(e.args[0]))
    if _admins.fetchone() is None:
        print ("No admins found on startup. Please add an admin using the following promts.")
        username = raw_input("Username: ")
        password = getpass.getpass("Password: ")
        try:
            conn.execute("insert into Admin (UUID, NAME, PASSWORDHASH) values ('{_UUID}', '{_Name}', '{_PWHash}');".format(_UUID = uuid.uuid4(), _Name = username, _PWHash = generate_password_hash(password)))
            conn.commit()
        except sqlite3.Error as e:
            print (str(e.args[0]))
        print("Thank you, Admin has been added.")
        username = None
        password = None
        
    app.run(host='127.0.0.1', port=8000)
    
    while True:
        pass