#!/usr/bin/env python

# -*- coding: utf-8 -*-
#"""
#Flask code adapted from: https://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972
#Created on Wed 14-02-2018
#
#@author: Bas Janssen
#"""

from flask import Flask, render_template, request, session, Markup
import sqlite3
import uuid
from datetime import timedelta


app = Flask(__name__)
app.secret_key = 'This is a really secret key for this app'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes = 5)

@app.route('/')
def index():
    if session.get('uuid'):
        pass
    else:
        session['uuid'] = uuid.uuid4()
    try:
        _photographers = conn.execute('''select ID, NAME from Photographers;''')
    except sqlite3.Error as e:
        return render_template('error.html', error = str(e.args[0]))
    _overview = "<table class='table table-hover'><tr><th>Photographers</th></tr>"
    _script = "<script>$(document).ready( function() {"
    for row in _photographers:
        try:
            _rating = conn.execute('''select avg(RATING) from Ratings where PHOTOGRAPHER={_Photographer} and DAY=date('now');'''.format(_Photographer=row[0]))
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        _currentRating = 0
        row2 = _rating.fetchone()
        if row2 is None:
            pass
        else:
            _currentRating = row2[0] or 0
        _overview = _overview + "<tr><td data-toggle='collapse' data-target='#{_photographer}' class='clickable'>{_photographer}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr>".format(_photographer = row[0])
        _script = _script + "$('{_photographer}').starRating({{starSize: 25, initialRating: {_rating}, disableAfterRate: false, callback: function(currentRating, $el){{$.post('addRating', {{'id': $el[0].id, 'rating': currentRating}});}}}});".format(_photographer = ".photo-rating-" + str(row[0]), _rating = _currentRating)
    _overview = _overview + "</table>"
    _script = _script + "});</script>"
    return render_template('index.html', overview = Markup(_overview), script=Markup(_script))

@app.route('/overview')
def overview():
    try:
        _photographers = conn.execute('''select ID, NAME from Photographers;''')
    except sqlite3.Error as e:
        return render_template('error.html', error = str(e.args[0]))
    _overview = "<table class='table table-hover'><tr><th>Photographers</th></tr>"
    _script = "<script>$(document).ready( function() {"
    for row in _photographers:
        try:
            _rating = conn.execute('''select avg(RATING) from Ratings where PHOTOGRAPHER={_Photographer} and DAY=date('now');'''.format(_Photographer=row[0]))
        except sqlite3.Error as e:
            return render_template('error.html', error = str(e.args[0]))
        _overview = _overview + "<tr><td data-toggle='collapse' data-target='#{_photographer}' class='clickable'>{_photographer}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr>".format(_photographer = row[0])
        _script = _script + "$('{_photographer}').starRating({{starSize: 25, readOnly: true, initialRating: {_rating}}});".format(_photographer = ".photo-rating-" + str(row[0]), _rating = _rating.fetchone()[0] or 0)
    _overview = _overview + "</table>"
    _script = _script + "});</script>"
    return render_template('index.html', overview = Markup(_overview), script=Markup(_script))

@app.route("/addRating", methods=['POST'])
def addRating():
    if session.get('uuid'):    
        try:
            conn.cursor().execute("insert or replace into Ratings (ID, RATING, USER, PHOTOGRAPHER, DAY) values ((select ID from Ratings where USER = '{_User}' and PHOTOGRAPHER = '{_Photographer}' and DAY=date('now')), '{_Rating}', '{_User}', (select ID from Photographers where NAME='{_Photographer}'), (date('now')));".format(_Photographer=request.form['id'], _Rating=request.form['rating'], _User=session.get('uuid')))
            conn.commit()
        except sqlite3.Error as e:
            print e.args[0]
            return render_template('error.html', error = str(e.args[0]))
        return "ok"
    else:
        return "invalid"

if __name__=="__main__":
    conn = sqlite3.connect('photovote.db')
    conn.execute('''PRAGMA foreign_keys = ON;''')
    conn.execute('''create table if not exists Admin(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, NAME TEXT NOT NULL, PASSWORDHASH TEXT NOT NULL);''') #The password must be hashed, plaintext can not be used.
    conn.execute('''create table if not exists Photographers(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, NAME TEXT NOT NULL);''')
    conn.execute('''create table if not exists Ratings(ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, RATING REAL NOT NULL, DAY TEXT NOT NULL, USER TEXT NOT NULL, PHOTOGRAPHER INT NOT NULL, FOREIGN KEY(PHOTOGRAPHER) REFERENCES PHOTOGRAPHERS(ID));''')
    app.run(host='127.0.0.1', port=8000)
    
    while True:
        pass