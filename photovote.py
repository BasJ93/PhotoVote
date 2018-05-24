#!/usr/bin/env python

# -*- coding: utf-8 -*-
#"""
#Flask code adapted from: https://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972
#Created on Wed 14-02-2018
#
#@author: Bas Janssen
#"""

from flask import Flask, render_template, request, session, Markup, redirect, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
from datetime import timedelta
import getpass

DATABASE = 'photovote.db'

#Ture means show the name, False means show the number
NameNumber = False

app = Flask(__name__)
app.secret_key = 'This is a really secret key for this app'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes = 360)

@app.route('/')
def index():
    global NameNumber
    if session.get('uuid'):
        pass
    else:
        session['uuid'] = uuid.uuid4()
    try:
        if(NameNumber):
            _photographers = query_db("select ID, NAME, NUMBER from Photographers order by NAME asc;")
        else:
            _photographers = query_db("select ID, NAME, NUMBER from Photographers order by NUMBER asc;")
    except sqlite3.Error as e:
        return render_template('error.html', error = str(e.args[0]))
    _overview = "<table class='table table-hover'>\n\t\t\t\t<tr><th>Photographers</th></tr>\n"
    _script = "<script>\n\t\t$(document).ready( function() {\n"
    for row in _photographers:
        try:
            row2 = query_db('''select RATING from Ratings where PHOTOGRAPHER=? and DAY=date('now') and USER=?;''', (row[0], session.get('uuid')), True)
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        _currentRating = 0
        if row2 is None:
            pass
        else:
            _currentRating = row2[0] or 0
        if NameNumber:
            _overview = _overview + "\t\t\t\t<tr>\n\t\t\t\t\t<td>{_name}</td>\n\t\t\t\t\t<td>\n\t\t\t\t\t\t<div id='{_photographer}' class='photo-rating-{_photographer}'></div>\n\t\t\t\t\t</td>\n\t\t\t\t</tr>\n".format(_photographer = row[0], _name = row[1])
        else:
            _overview = _overview + "<tr><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr>".format(_photographer = row[0], _name = row[2])
        _script = _script + "\t\t\t$('{_photographer}').starRating({{useFullStars: true, starSize: 25, initialRating: {_rating}, disableAfterRate: false, callback: function(currentRating, $el){{$.post('addRating', {{'id': $el[0].id, 'rating': currentRating}});}}}});\n".format(_photographer = ".photo-rating-" + str(row[0]), _rating = _currentRating)
    _overview = _overview + "\t\t\t</table>"
    _script = _script + "\t\t});\n\t</script>"
    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'><span class='navbar-brand'>Photo Vote</span><button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button><div class='collapse navbar-collapse' id='collapsingNavbar'><ul class='navbar-nav ml-auto'><li class='nav-item'><a class='nav-link active' href='/login'>Login</a></li></ul></div></nav>"
    return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), script=Markup(_script))

@app.route('/overview')
def overview():
    global NameNumber
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return redirect('/')
            else:
                try:
                    _photographers = query_db("select Photographers.ID, NAME, NUMBER, avg(RATING), sum(RATING), COUNT(RATING) from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') group by Photographers.ID order by sum(RATING) desc;")
                except sqlite3.Error as e:
                    return render_template('error.html', error = str(e.args[0]))
                _overview = "<div class='table-responsive'><table class='table table-hover'><thead><tr><th id='PhotographerHead'>Photographer</th><th>Average score</th></tr></thead>"
                _script = "<script>$(document).ready( function() {"
                for row in _photographers:
                    if NameNumber:
                        _overview = _overview + "<tbody><tr class='clickable' data-toggle='collapse' data-target='#options-{_photographer}' aria-expanded='false' aria-controls='options-{_photographer}'><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr></tbody><tbody id='options-{_photographer}' class='collapse'><tr><td>Votes: {_votes}</td><td>Total Score: {_TotalScore}</td></tr><tr><td><button type='button' class='btn btn-danger' id='btn-remove-{_photographer}'>Remove</button></td><td><form action='/change_photographer'><input type='hidden' id='ExistingID' name='ExistingID' value='{_photographer}'><button type='submit' class='btn btn-warning' id='btn-rename-{_photographer}'>Rename</button></form></td></tr></tbody>".format(_photographer = row[0], _name = row[1], _TotalScore = row[4] or 0, _votes = row[5] or 0)
                    else:
                        _overview = _overview + "<tbody><tr class='clickable' data-toggle='collapse' data-target='#options-{_photographer}' aria-expanded='false' aria-controls='options-{_photographer}'><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr></tbody><tbody id='options-{_photographer}' class='collapse'><tr><td>Votes: {_votes}</td><td>Total Score: {_TotalScore}</td></tr><tr><td><button type='button' class='btn btn-danger' id='btn-remove-{_photographer}'>Remove</button></td><td><form action='/change_photographer'><input type='hidden' id='ExistingID' name='ExistingID' value='{_photographer}'><button type='submit' class='btn btn-warning' id='btn-rename-{_photographer}'>Rename</button></form></td></tr></tbody>".format(_photographer = row[0], _name = row[2], _TotalScore = row[4] or 0, _votes = row[5] or 0)
                    _script = _script + "$('{_photographer}').starRating({{starSize: 25, readOnly: true, initialRating: {_rating}}});".format(_photographer = ".photo-rating-" + str(row[0]), _rating = row[3] or 0)
                _overview = _overview + "</table></div>"
                _script = _script + "$('.btn-danger').click(function(event){$.ajax({method: 'POST', url: 'removePhotographer', data: {'id': $(event.target).attr('id')}}).done(function(html){location.reload(true)});});"
                _script = _script + "if($(window).width() < 544){$('#PhotographerHead').text('Photo');}"
                _script = _script + "$('#NameNumber').change(function(){$.ajax({method: 'POST', url: 'changenamenumber', data: {'state': this.checked}}).done(function(html){window.location.reload(true);console.log(html)});});});</script>"
                if NameNumber:
                    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'>\n\
                <a class='navbar-brand' href='/'>Photo Vote</a>\n\
                <button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button>\n\
                <div class='collapse navbar-collapse' id='collapsingNavbar'>\n\
                    <ul class='navbar-nav ml-auto'>\n\
                        <li class='nav-item'><div class='btn-group btn-group-toggle' data-toggle='buttons'><label class='btn btn-primary active'><input name='NameNumber' id='NameNumber' type='checkbox' autocomplete='off' checked='{_state}'/>Show Names</label></div></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/export_results' target='_blank'>Export Results</a></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/add_photographer'>Add Photographer</a></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/add_admin'>Add Admin</a></li>\n\
                        <li class='nav-item'><a class='nav-link active' href='/logout'>Logout</a></li>\n\
                    </ul>\n\
                </div>\n\
            </nav>".format(_state = NameNumber)
                else:
                    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'>\n\
                <a class='navbar-brand' href='/'>Photo Vote</a>\n\
                <button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button>\n\
                <div class='collapse navbar-collapse' id='collapsingNavbar'>\n\
                    <ul class='navbar-nav ml-auto'>\n\
                        <li class='nav-item'><div class='btn-group btn-group-toggle' data-toggle='buttons'><label class='btn btn-primary'><input name='NameNumber' id='NameNumber' type='checkbox' autocomplete='off' checked='{_state}'/>Show Names</label></div></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/export_results' target='_blank'>Export Results</a></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/add_photographer'>Add Photographer</a></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/add_admin'>Add Admin</a></li>\n\
                        <li class='nav-item'><a class='nav-link active' href='/logout'>Logout</a></li>\n\
                    </ul>\n\
                </div>\n\
            </nav>".format(_state = NameNumber)
                return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), script=Markup(_script))
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/addRating", methods=['POST'])
def addRating():
    if session.get('uuid'):    
        try:
            query_db("insert or replace into Ratings (ID, RATING, USER, PHOTOGRAPHER, DAY) values ((select ID from Ratings where USER = ? and PHOTOGRAPHER = ? and DAY=date('now')), ?, ?, ?, (date('now')));", (session.get('uuid'), request.form['id'], request.form['rating'] , session.get('uuid'), request.form['id']))
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
            _pw_hashes = query_db("select PASSWORDHASH, UUID from Admin where NAME=?;", (_username,), True)
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        if _pw_hashes is None:
            return redirect('/login')
        else:
            pw_hash = _pw_hashes[0]
            uuid = _pw_hashes[1]
            if check_password_hash(pw_hash, _password):
                session['user'] = _username
                session['uuid'] = uuid
                return redirect('/overview')
            else:
                return render_template('error.html',error = 'Invalid password.')
    
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
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
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return redirect('/')
            else:
                if request.method == 'POST':
                    try:
                        photographer = request.form['inputPhotographer']
                        number = request.form['inputNumber']
                    except Exception as e:
                        return render_template('error.html', error = str(e))
                    try:
                        query_db("insert into Photographers (NAME, NUMBER) values (?, ?);", (photographer, number))
                    except sqlite3.Error as e:
                        return render_template('error.html', error = str(e.args[0]))
                    return redirect('/overview')
                    
                return render_template('add_photographer.html', path=Markup("/add_photographer"), defaultPhotographer=Markup("Photographer"), defaultNumber=Markup("1"), ExistingID=Markup(""), action=Markup("add"))
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/change_photographer", methods=['GET', 'POST'])
def change_photographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return redirect('/')
            else:
                if request.method == 'POST':
                    try:
                        photographer = request.form['inputPhotographer']
                        number = request.form['inputNumber']
                        ExistingID = request.form["ExistingID"]
                    except Exception as e:
                        return render_template('error.html', error = str(e))
                    try:
                        query_db("update Photographers set NAME=?, NUMBER=? WHERE ID=?;", (photographer, number, ExistingID))
                    except sqlite3.Error as e:
                        return render_template('error.html', error = str(e.args[0]))
                    return redirect('/overview')
                
                currentValues = query_db("select NAME, NUMBER from Photographers WHERE ID=?", (request.args['ExistingID'],), True)
                return render_template('add_photographer.html', path=Markup("/change_photographer"),  defaultPhotographer=Markup(currentValues['NAME']), defaultNumber=Markup(currentValues['NUMBER']), ExistingID=Markup(request.args['ExistingID']), action=Markup("change"))
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/removePhotographer", methods=['POST'])
def removePhotographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return "invalid"
            else:
                    try:
                        data = request.form['id'].split("-")
                        photographer = data[2]
                    except Exception as e:
                        print (e)
                        return "invalid"
                    try:
                        #I still want to look into a non destructive delete.
                        query_db("delete from Ratings where PHOTOGRAPHER=?;", [photographer])
                        query_db("delete from Photographers where ID=?;", [photographer])
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
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return redirect('/')
            else:
                if request.method == 'POST':
                    try:
                        _username = request.form['inputUsername']
                        _password = request.form['inputPassword']
                    except Exception as e:
                        return render_template('error.html', error = str(e))
                    try:
                        query_db("insert into Admin (UUID, NAME, PASSWORDHASH) values (?, ?, ?);", (str(uuid.uuid4()), _username, generate_password_hash(_password)))
                    except sqlite3.Error as e:
                        return render_template('error.html', error = str(e.args[0]))
                    return redirect('/overview')
                    
                return render_template("login.html", path=Markup("add_admin"), action=Markup("Add Admin"))
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/changenamenumber", methods=['POST'])
def changenamenumber():
    global NameNumber
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return "nok"
            else:
                if request.method == 'POST':
                    try:
                        _state = request.form['state']
                    except Exception as e:
                        return "nok"
                    try:
                            query_db("update Settings Set VALUE=? where NAME='NameNumber';", (_state,))
                    except sqlite3.Error as e:
                        return "nok"
                    if _state == "false":
                        NameNumber = False
                    else:
                        NameNumber = True
                    return "ok"
                else:
                    return "nok"
        else:
            return "nok"
    else:
        return "nok"

@app.route("/export_results")
def export_results():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                return render_template('error.html', error = str(e.args[0]))
            if _admins is None:
                return "nok"
            else:
                csv = "Name, Number, Avg Points, Total Points, Number of votes\n"
                results = query_db("select Photographers.ID, NAME, NUMBER, avg(RATING) AS AVG, sum(RATING) AS TOTAL, COUNT(RATING) AS VOTES from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') group by Photographers.ID order by sum(RATING) desc;")
                for row in results:
                    csv = csv + "{_Name}, {_Number}, {_Avg}, {_Total}, {_Count}\n".format(_Name = row['NAME'], _Number=row['Number'], _Avg=row['AVG'], _Total=row['TOTAL'], _Count=row['VOTES'])
                response = make_response(csv)
                cd = 'attachment; filename=results.csv'
                response.headers['Content-Disposition'] = cd
                response.mimetype='text/csv'
                
                return response

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    #print(query.replace('?', '%s') % args)
    try:
        cur = get_db().execute(query, args)
        get_db().commit()
    except sqlite3.Error as e:
        print e
        return None
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__=="__main__":
    with app.app_context():
        query_db('''PRAGMA foreign_keys = ON;''')
        query_db('''create table if not exists Admin(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, UUID TEXT, NAME TEXT, PASSWORDHASH TEXT);''') #The password must be hashed, plaintext can not be used.
        query_db('''create table if not exists Photographers(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, NAME TEXT NOT NULL, NUMBER INTEGER NOT NULL);''')
        query_db('''create table if not exists Ratings(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, RATING REAL NOT NULL, DAY TEXT NOT NULL, USER TEXT NOT NULL, PHOTOGRAPHER INT NOT NULL, FOREIGN KEY(PHOTOGRAPHER) REFERENCES PHOTOGRAPHERS(ID));''')
        query_db('''create table if not exists Settings(NAME TEXT PRIMARY KEY UNIQUE NOT NULL, VALUE TEXT NOT NULL);''')
        query_db('''insert into Settings (NAME, VALUE) values ('NameNumber', 'false');''')
    
        try:
            _admins = query_db("select ID from Admin;", (), True)
        except sqlite3.Error as e:
            print (str(e.args[0]))
        if _admins is None:
            print ("No admins found on startup. Please add an admin using the following promts.")
            username = raw_input("Username: ")
            password = getpass.getpass("Password: ")
            try:
                query_db("insert into Admin (UUID, NAME, PASSWORDHASH) values (?, ?, ?);", (str(uuid.uuid4()), username, generate_password_hash(password)))
            except sqlite3.Error as e:
                print (str(e.args[0]))
            print("Thank you, Admin has been added.")
            username = None
            password = None
        
        try:
            _NameNumber = query_db("select VALUE from Settings where NAME=?;", ('NameNumber',), one=True)    
            if _NameNumber is None:
                print "Something went wrong with the settings."
            else:
                if _NameNumber['VALUE'] == "true":
                    NameNumber = True
                else:
                    NameNumber = False
        except sqlite3.Error as e:
            print (str(e.args[0]))
    app.run(host='127.0.0.1', port=8000)
    
    while True:
        pass