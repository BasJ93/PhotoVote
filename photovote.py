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
from werkzeug.contrib.fixers import ProxyFix
import sqlite3
import uuid
from datetime import timedelta
import getpass
import logging

#Ture means show the name, False means show the number
NameNumber = False

app = Flask(__name__, static_url_path='', instance_relative_config=True) #Set the static url path to /. This will present the static folder as part of /
app.config.from_object('config')
app.config.from_pyfile('config.py')
if app.config['PROXY']:
    app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = 'This is a really secret key for this app'

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes = 360)

#In the mobile mode it changes the rows into cards.

@app.route('/')
def index():
    global NameNumber
    if session.get('uuid'):
        pass
    else:
        session['uuid'] = str(uuid.uuid4())
    _overview = "<div id='tableOverview' class='table-responsive'>\n</div>"
    _script = "<script>\n\
                    if('serviceWorker' in navigator) {\n\
                        window.addEventListener('load', function() {\n\
                            navigator.serviceWorker.register('/sw.js').then(function(registration){\n\
                                console.log('ServiceWorker registration successfull with scope: ', registration.scope);}, function(err) {\n\
                                    console.log('ServiceWoerker registration failed: ', err);\n\
                                });\n\
                            });\n\
                        }\n\
                        let deferredPrompt;\n\
\n\
                        window.addEventListener('beforeinstallprompt', (e) => {\n\
                          // Prevent Chrome 67 and earlier from automatically showing the prompt\n\
                          e.preventDefault();\n\
                          // Stash the event so it can be triggered later.\n\
                          deferredPrompt = e;\n\
                          $('#inner-container').prepend(\"<button class='btn btn-info' style='width:100%;' click='triggerInstall'>Add to homescreen</button>\");\n\
                        });\n\
                        function triggerInstall() {\n\
                            $('.btn-info').remove();\n\
                            deferredPrompt.prompt();\n\
                              // Wait for the user to respond to the prompt\n\
                              deferredPrompt.userChoice\n\
                                .then((choiceResult) => {\n\
                                  if (choiceResult.outcome === 'accepted') {\n\
                                    console.log('User accepted the A2HS prompt');\n\
                                  } else {\n\
                                    console.log('User dismissed the A2HS prompt');\n\
                                  }\n\
                                  deferredPrompt = null;\n\
                                });\n\
                        }\n\
\n\
                    $(document).ready(function() {\n\
                        if($(window).width() < 544){\n\
                                $('body').css('padding-top', '0px');\n\
                            }\n\
                            else{\n\
                                $('.container').removeClass('m-0 p-0');\n\
                                $('.header').removeClass('m-o p-o');\n\
                                $('.jumbotron').removeClass('m-0 p-0');\n\
                        }\n\
                        $('#LoginBtn').click(\n\
    		 			function(event) {\n\
    		 				$.ajax({method: 'POST', url: 'login', data: {'inputUsername': $('#inputUsername').val(), 'inputPassword': $('#inputPassword').val()}}).done(\n\
    		 					function(data){\n\
    			 					if(data === 'ok')\n\
                                             {\n\
                                                 window.location = 'overview';\n\
                                             }\n\
                                             else\n\
                                             {\n\
                                                \n\
                                             }\n\
    	 							});\n\
    					});\n\
                        updateTable();\n\
                    });\n\
                    function updateTable() {\n\
                         $.get('/getVote', function(data) {$('#tableOverview').html(data);});\n\
                     }\n\
           </script>"
    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'><span class='navbar-brand'>Photo Vote</span><button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button><div class='collapse navbar-collapse' id='collapsingNavbar'><ul class='navbar-nav ml-auto'>\n\
    <li class='nva-item'><button type='button' class='btn btn-primary' data-toggle='modal' data-target='#loginModal'>login</button>\n\
    </ul></div></nav>"
    _modals = "<!-- The Login Modal -->\
		<div class='modal' id='loginModal' role='dialog'>\
		  <div class='modal-dialog'>\
			<div class='modal-content'>\
\
			  <!-- Modal Header -->\
			  <div class='modal-header bg-primary'>\
				<h4 class='modal-title text-white' id='titleLogin'>Login</h4>\
				<button type='button' class='close' data-dismiss='modal'>&times;</button>\
			  </div>\
\
			  <!-- Modal body -->\
			  <div class='modal-body bg-light'>\
			  	<form  class='form-signin'>\
					<label for='inputUsername' class='sr-only'>Username</label>\n\
                          <input type='text' name='inputUsername' id='inputUsername' class='form-control' placeholder='Username' required autofocus>\n\
                          <label for='inputPassword' class='sr-only'>Password</label>\n\
                          <input type='password' name='inputPassword' id='inputPassword' class='form-control' placeholder='Password' required>\n\
			  	</form>\
			  </div>\
     \
			  <!-- Modal footer -->\
			  <div class='modal-footer'>\
				<button type='button' class='btn btn-primary' id='LoginBtn'>Login</button><button type='button' class='btn btn-danger' data-dismiss='modal'>Close</button>\
			  </div>\
\
			</div>\
		  </div>\
		</div>\n"
    return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), alerts = Markup(""), modals = Markup(_modals), script=Markup(_script))

@app.route('/overview')
def overview():
    global NameNumber
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return "nok"
            if _admins is None:
                return "nok"
            else:
                _overview = "<div id='tableOverview' class='table-responsive'>\n</div>"
                _script = "<script>"
                _script = _script + "$(document).ready(function() {\n"
                _script = _script + "if($(window).width() < 544){\n\
                            $('body').css('padding-top', '0px');}else{$('.container').removeClass('m-0 p-0');$('.header').removeClass('m-o p-o');$('.jumbotron').removeClass('m-0 p-0');\n\
                        }\n"
                _script = _script + "\t\t\t\t\t\t$('body').on('click', '.btn-warning', function(event){\n\t\t\t\t\t\t\tvar IDnumber = $(event.target).attr('id').split('-');$('#ExistingID').val(IDnumber[2]);\n$('#inputChangePhotographer').val($('#Name-ID-'+IDnumber[2]).val());\n$('#inputChangeNumber').val($('#Number-ID-'+IDnumber[2]).val());\n$('#changePhotographerModal').modal('show');\n\t\t\t\t\t\t});\n"
                _script = _script + "\t\t\t\t\t\t$('body').on('click', '.btn-danger', function(event){\n\t\t\t\t\t\t\t$.ajax({method: 'POST', url: 'removePhotographer', data: {'id': $(event.target).attr('id')}}).done(function(html){updateTable()\n});})\n"#
                _script = _script + "\t\t\t\t\t\tif($(window).width() < 544){$('#PhotographerHead').text('Photo');}\n"
                _script = _script + "\t\t\t\t\t\t$('#NameNumber').change(function(){\n\t\t\t\t\t\t\t$.ajax({method: 'POST', url: 'changenamenumber', data: {'state': this.checked}}).done(function(html){updateTable();})\n\t\t\t\t\t\t;});\n"
                _script = _script + "\t\t\t\t\t\t$('#addPhotographerBtn').click(\n\
    		 			function(event) {\n\
    		 				$.ajax({method: 'POST', url: 'addPhotographer', data: {'inputPhotographer': $('#inputPhotographer').val(), 'inputNumber': $('#inputNumber').val()}}).done(\n\
    		 					function(html){\n\
    			 					//Trigger a toast popup confirming the add was successful.\n\
                                           $('#addPhotographerModal').modal('hide');\n\
    		 						updateTable()\n\
    	 							});\n\
    					});\n\
                         $('#changePhotographerBtn').click(\n\
        		 			function(event) {\n\
        		 				$.ajax({method: 'POST', url: 'changePhotographer', data: {'ExistingID': $('#ExistingID').val(), 'inputPhotographer': $('#inputChangePhotographer').val(), 'inputNumber': $('#inputChangeNumber').val()}}).done(\n\
        		 					function(html){\n\
        			 					//Trigger a toast popup confirming the add was successful.\n\
                                                $('#changePhotographerModal').modal('hide');\n\
        			 					updateTable()\n\
        	 							});\n\
    					});\n\
        				$('#addAdminBtn').click(\n\
        		 			function(event) {\n\
        		 				$.ajax({method: 'POST', url: 'addAdmin', data: {'inputUsername': $('#inputUsername').val(), 'inputPassword': $('#inputPassword').val()}}).done(\n\
        		 					function(html){\n\
        		 						//Trigger a toast popup confirming the add was successful.\n\
        		 						//Close the modal.\n\
        		 						//location.reload(true)\n\
        		 						$('#addAdminModal').modal('hide');\n\
        		 						$('#alertAdminSuccess').addClass('show');\n\
        	 							});\n\
        					});\n\
                         updateTable();\n\
                     });\n\
                     function updateTable() {\n\
                     \t$.get('/getOverview', function(data) {$('#tableOverview').html(data);});\n\
                     }\n\
           </script>"
                if NameNumber:
                    _navbar = "<nav class='navbar navbar-expand-md bg-primary navbar-dark'>\n\
                <a class='navbar-brand' href='/'>Photo Vote</a>\n\
                <button class='navbar-toggler navbar-toggler-right' type='button' data-toggle='collapse' data-target='#collapsingNavbar'><span class='navbar-toggler-icon'></span></button>\n\
                <div class='collapse navbar-collapse' id='collapsingNavbar'>\n\
                    <ul class='navbar-nav ml-auto'>\n\
                        <li class='nav-item'><div class='btn-group btn-group-toggle' data-toggle='buttons'><label class='btn btn-primary active'><input name='NameNumber' id='NameNumber' type='checkbox' autocomplete='off' checked='{_state}'/>Show Names</label></div></li>\n\
                        <li class='nav-item'><a class='nav-link' href='/export_results' target='_blank'>Export Results</a></li>\n\
                        <li class='nva-item'><button type='button' class='btn btn-primary' data-toggle='modal' data-target='#addPhotographerModal'>Add Photographer</button>\n\
                        <li class='nva-item'><button type='button' class='btn btn-primary' data-toggle='modal' data-target='#addAdminModal'>Add Admin</button>\n\
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
                        <!--<li class='nav-item'><a class='nav-link' href='/addPhotographer'>Add Photographer</a></li>\n-->\
                        <li class='nav-item'><a class='nav-link' href='/export_results' target='_blank'>Export Results</a></li>\n\
                        <li class='nva-item'><button type='button' class='btn btn-primary' data-toggle='modal' data-target='#addPhotographerModal'>Add Photographer</button>\n\
                        <li class='nva-item'><button type='button' class='btn btn-primary' data-toggle='modal' data-target='#addAdminModal'>Add Admin</button>\n\
                        <li class='nav-item'><a class='nav-link active' href='/logout'>Logout</a></li>\n\
                    </ul>\n\
                </div>\n\
            </nav>".format(_state = NameNumber)
                _alerts = "<div id='alertAdminSuccess' class='alert alert-success alert-dismissible fade collapse' role='alert'>\n\
				<p class='mb-0'>Admin added</p>\n\
				<button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>&times;</span></button>\n\
			</div>\n\
			<div id='alertPhotographerSucces' class='alert alert-success alert-dismissible fade collapse' role='alert'>\n\
				<p class='mb-0'>Photographer added</p>\n\
				<button type='button' class='close' data-dismiss='alert' aria-label='Close'><span aria-hidden='true'>&times;</span></button>\n\
			</div>\n"
                _modals = "<!-- The Add Photographer Modal -->\
		<div class='modal' id='addPhotographerModal'>\
		  <div class='modal-dialog'>\
			<div class='modal-content'>\
\
			  <!-- Modal Header -->\
			  <div class='modal-header'>\
				<h4 class='modal-title' id='titleAddPhotographer'>Add Photographer</h4>\
				<button type='button' class='close' data-dismiss='modal'>&times;</button>\
			  </div>\
\
			  <!-- Modal body -->\
			  <div class='modal-body'>\
			  	<form  class='form-signin'>\
					<label for='inputPhotographer' class='sr-only'>Photographer</label>\
				  	<input type='text' name='inputPhotographer' id='inputPhotographer' class='form-control' placeholder='Photographer' required autofocus>\
				  	<label for='inputNumber' class='sr-only'>Photo number</label>\
				  	<input type='text' name='inputNumber' id='inputNumber' class='form-control' placeholder='1' required>\
			  	</form>\
			  </div>\
\
			  <!-- Modal footer -->\
			  <div class='modal-footer'>\
				<button type='button' class='btn btn-success' id='addPhotographerBtn'>Add</button><button type='button' class='btn btn-danger' data-dismiss='modal'>Close</button>\
			  </div>\
\
			</div>\
		  </div>\
		</div>\
  <!-- The Change Photographer Modal -->\
		<div class='modal' id='changePhotographerModal'>\
		  <div class='modal-dialog'>\
			<div class='modal-content'>\
\
			  <!-- Modal Header -->\
			  <div class='modal-header'>\
				<h4 class='modal-title' id='titleChangePhotographer'>Change Photographer</h4>\
				<button type='button' class='close' data-dismiss='modal'>&times;</button>\
			  </div>\
\
			  <!-- Modal body -->\
			  <div class='modal-body'>\
			  	<form  class='form-signin'>\
					<label for='inputChangePhotographer' class='sr-only'>Photographer</label>\
				  	<input type='text' name='inputChangePhotographer' id='inputChangePhotographer' class='form-control' placeholder='Photographer' required autofocus>\
				  	<label for='inputChangeNumber' class='sr-only'>Photo number</label>\
				  	<input type='text' name='inputChangeNumber' id='inputChangeNumber' class='form-control' placeholder='1' required>\
                           <input type='hidden' name='ExistingID' id='ExistingID'>\n\
			  	</form>\
			  </div>\
\
			  <!-- Modal footer -->\
			  <div class='modal-footer'>\
				<button type='button' class='btn btn-success' id='changePhotographerBtn'>Change</button><button type='button' class='btn btn-danger' data-dismiss='modal'>Close</button>\
			  </div>\
\
			</div>\
		  </div>\
		</div>\
		<!-- The Add Admin Modal -->\
		<div class='modal' id='addAdminModal'>\
		  <div class='modal-dialog'>\
			<div class='modal-content'>\
\
			  <!-- Modal Header -->\
			  <div class='modal-header'>\
				<h4 class='modal-title'>Add Admin</h4>\
				<button type='button' class='close' data-dismiss='modal'>&times;</button>\
			  </div>\
\
			  <!-- Modal body -->\
			  <div class='modal-body'>\
			  	<form  class='form-signin'>\
					<label for='inputPhotographer' class='sr-only'>Admin</label>\
				  	<input type='text' name='inputUsername' id='inputUsername' class='form-control' placeholder='Admin' required autofocus>\
				  	<label for='inputNumber' class='sr-only'>Password</label>\
				  	<input type='password' name='inputPassword' id='inputPassword' class='form-control' placeholder='Password' required>\
			  	</form>\
			  </div>\
\
			  <!-- Modal footer -->\
			  <div class='modal-footer'>\
				<button type='button' class='btn btn-success' id='addAdminBtn'>Add</button><button type='button' class='btn btn-danger' data-dismiss='modal'>Close</button>\
			  </div>\
\
			</div>\
		  </div>\
		</div>"
                return render_template('index.html', navbar = Markup(_navbar), overview = Markup(_overview), alerts = Markup(_alerts), modals = Markup(_modals), script = Markup(_script))
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
            logging.error(str(e.args[0]))
            return "nok"
        return "ok"
    else:
        return "invalid"

@app.route("/login", methods=['POST'])
def login():
    try:
        _username = request.form['inputUsername']
        _password = request.form['inputPassword']
    except Exception as e:
        return "nok"#render_template('error.html', error = str(e))        
    try:
        _pw_hashes = query_db("select PASSWORDHASH, UUID from Admin where NAME=?;", (_username,), True)
    except sqlite3.Error as e:
        logging.error(str(e.args[0]))
        return "nok"#redirect('/login')
    if _pw_hashes is None:
        return "nok"#redirect('/login')
    else:
        pw_hash = _pw_hashes[0]
        uuid = _pw_hashes[1]
        if check_password_hash(pw_hash, _password):
            session['user'] = _username
            session['uuid'] = uuid
            return "ok"#redirect('/overview')
    
@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route("/addPhotographer", methods=['POST'])
def add_photographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return "nok"
            if _admins is None:
                return "nok"
            else:
                try:
                    photographer = request.form['inputPhotographer']
                    number = request.form['inputNumber']
                except Exception as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                try:
                    query_db("insert into Photographers (NAME, NUMBER) values (?, ?);", (photographer, number))
                except sqlite3.Error as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                return "ok"
                    
        else:
            return "nok"
    else:
        return "nok"

@app.route("/changePhotographer", methods=['POST'])
def change_photographer():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return "nok"
            if _admins is None:
                return "nok"
            else:
                try:
                    photographer = request.form['inputPhotographer']
                    number = request.form['inputNumber']
                    ExistingID = request.form["ExistingID"]
                except Exception as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                try:
                    query_db("update Photographers set NAME=?, NUMBER=? WHERE ID=?;", (photographer, number, ExistingID))
                except sqlite3.Error as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                return "ok"
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
                logging.error(str(e.args[0]))
            if _admins is None:
                return "nok"
            else:
                    try:
                        data = request.form['id'].split("-")
                        photographer = data[2]
                    except Exception as e:
                        logging.error(str(e.args[0]))
                        return "nok"
                    try:
                        #I still want to look into a non destructive delete.
                        query_db("delete from Ratings where PHOTOGRAPHER=?;", [photographer])
                        query_db("delete from Photographers where ID=?;", [photographer])
                    except sqlite3.Error as e:
                        logging.error(str(e.args[0]))
                        return "nok"
                    return "ok"
        else:
            return "nok"

@app.route('/getOverview')
def getOverview():
    global NameNumber
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return "nok"
            if _admins is None:
                return "nok"
            else:
                try:
                    _photographers = query_db("select Photographers.ID, NAME, NUMBER, avg(RATING), sum(RATING), COUNT(RATING) from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') group by Photographers.ID order by sum(RATING) desc;")
                except sqlite3.Error as e:
                    return render_template('error.html', error = str(e.args[0]))
                _script = "<script>"
                _overview = "<table class='table table-hover'><thead><tr><th id='PhotographerHead'>Photographer</th><th>Average score</th></tr></thead>"
                _script = _script + "$(document).ready(function() {\n\
            if($(window).width() < 544){$('#PhotographerHead').text('Photo');}\n"
                for row in _photographers:
                    if NameNumber:
                        _overview = _overview + "<tbody><tr class='clickable' data-toggle='collapse' data-target='#options-{_photographer}' aria-expanded='false' aria-controls='options-{_photographer}'><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr></tbody><tbody id='options-{_photographer}' class='collapse'><tr><td>Votes: {_votes}</td><td>Total Score: {_TotalScore}</td></tr><tr><td><button type='button' class='btn btn-danger' id='btn-remove-{_photographer}'>Remove</button></td><td><input type='hidden' id='Number-ID-{_photographer}' value='{_number}'><input type='hidden' id='Name-ID-{_photographer}' value='{_name}'><button class='btn btn-warning' id='btn-rename-{_photographer}'>Rename</button></td></tr></tbody>".format(_photographer = row[0], _name = row[1], _number = row[2], _TotalScore = row[4] or 0, _votes = row[5] or 0)
                    else:
                        _overview = _overview + "<tbody><tr class='clickable' data-toggle='collapse' data-target='#options-{_photographer}' aria-expanded='false' aria-controls='options-{_photographer}'><td>{_number}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr></tbody><tbody id='options-{_photographer}' class='collapse'><tr><td>Votes: {_votes}</td><td>Total Score: {_TotalScore}</td></tr><tr><td><button type='button' class='btn btn-danger' id='btn-remove-{_photographer}'>Remove</button></td><td><input type='hidden' id='Number-ID-{_photographer}' value='{_number}'><input type='hidden' id='Name-ID-{_photographer}' value='{_name}'><button class='btn btn-warning' id='btn-rename-{_photographer}'>Rename</button></td></tr></tbody>".format(_photographer = row[0], _name = row[1], _number = row[2], _TotalScore = row[4] or 0, _votes = row[5] or 0)
                    _script = _script + "\t\t\t\t\t\t$('{_photographer}').starRating({{starSize: 25, readOnly: true, initialRating: {_rating}}});\n".format(_photographer = ".photo-rating-" + str(row[0]), _rating = row[3] or 0)
                _overview = _overview + "</table>"
                _script = _script + "});</script>"
                _html = _overview + _script
                return _html
        else:
            return "nok"
    else:
        return "nok"

@app.route("/getVote")
def getVote():
    _overview = "<table class='table table-hover'>\n\t\t\t\t<tr><th id='PhotographerHead'>Photographers</th></tr>\n"
    _script = "<script>\n\t\t$(document).ready( function() {\n"
    _script = _script + "if($(window).width() < 544){$('#PhotographerHead').text('Photo');}\n"
    try:
        if(NameNumber):
            _photographers = query_db("select Photographers.ID AS ID, NAME, NUMBER, RATING from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') and Ratings.USER=? order by NAME asc;", (session.get('uuid'),))
        else:
            _photographers = query_db("select Photographers.ID AS ID, NAME, NUMBER, RATING from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') and Ratings.USER=? order by NUMBER asc;", (session.get('uuid'),))
    except sqlite3.Error as e:
        logging.error(str(e.args[0]))
        return "nok"
    for row in _photographers:
        _currentRating = row[3] or 0
        if NameNumber:
            _overview = _overview + "\t\t\t\t<tr>\n\t\t\t\t\t<td>{_name}</td>\n\t\t\t\t\t<td>\n\t\t\t\t\t\t<div id='{_photographer}' class='photo-rating-{_photographer}'></div>\n\t\t\t\t\t</td>\n\t\t\t\t</tr>\n".format(_photographer = row[0], _name = row[1])
        else:
            _overview = _overview + "<tr><td>{_name}</td><td><div id='{_photographer}' class='photo-rating-{_photographer}'></div></td></tr>".format(_photographer = row[0], _name = row[2])
        _script = _script + "\t\t\t$('{_photographer}').starRating({{useFullStars: true, starSize: 25, initialRating: {_rating}, disableAfterRate: false, callback: function(currentRating, $el){{$.post('addRating', {{'id': $el[0].id, 'rating': currentRating}});}}}});\n".format(_photographer = ".photo-rating-" + str(row[0]), _rating = _currentRating)
    _overview = _overview + "\t\t\t</table>"
    _script = _script + "\t\t});\n\t</script>" 
    _html = _overview + _script
    return _html

@app.route("/addAdmin", methods=['POST'])
def add_admin():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return "nok"
            if _admins is None:
                return "nok"
            else:
                try:
                    _username = request.form['inputUsername']
                    _password = request.form['inputPassword']
                except Exception as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                try:
                    query_db("insert into Admin (UUID, NAME, PASSWORDHASH) values (?, ?, ?);", (str(uuid.uuid4()), _username, generate_password_hash(_password)))
                except sqlite3.Error as e:
                    logging.error(str(e.args[0]))
                    return "nok"
                return "ok"

        else:
            return "nok"
    else:
        return "nok"

@app.route("/changenamenumber", methods=['POST'])
def changenamenumber():
    global NameNumber
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
            if _admins is None:
                return "nok"
            try:
                _state = request.form['state']
            except Exception as e:
                logging.error(str(e.args[0]))
                return "nok"
            try:
                    query_db("update Settings Set VALUE=? where NAME='NameNumber';", (_state,))
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
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

@app.route("/export_results")
def export_results():
    if session.get('uuid'):
        if session.get('user'):
            try:
                _admins = query_db("select ID from Admin where NAME=? and UUID=?;", (session.get('user'), session.get('uuid')), True)
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
                return None
            if _admins is None:
                logging.warning("Request failed: User not logged in as admin.")
                return "nok"
            else:
                csv = "Name, Number, Avg Points, Total Points, Number of votes\n"
                results = query_db("select Photographers.ID, NAME, NUMBER, avg(RATING) AS AVG, sum(RATING) AS TOTAL, COUNT(RATING) AS VOTES from Photographers left join Ratings on Ratings.Photographer = Photographers.ID and Ratings.DAY=date('now') group by Photographers.ID order by sum(RATING) desc;")
                for row in results:
                    csv = csv + "{_Name}, {_Number}, {_Avg}, {_Total}, {_Count}\n".format(_Name = row['NAME'], _Number = row['Number'], _Avg = row['AVG'] or 0, _Total = row['TOTAL'] or 0, _Count = row['VOTES'] or 0)
                response = make_response(csv)
                cd = 'attachment; filename=results.csv'
                response.headers['Content-Disposition'] = cd
                response.mimetype='text/csv'
                
                return response

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    logging.debug(query.replace('?', '%s') % args)
    try:
        cur = get_db().execute(query, args)
        get_db().commit()
    except sqlite3.Error as e:
        logging.error(str(e.args[0]))
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
    if app.config['DEBUG']:
        logging.basicConfig(filename='photovote.log', level=logging.DEBUG)
    else:
        logging.basicConfig(filename='photovote.log', level=logging.INFO)
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
            logging.error(str(e.args[0]))
        if _admins is None:
            print ("No admins found on startup. Please add an admin using the following promts.")
            username = raw_input("Username: ")
            password = getpass.getpass("Password: ")
            try:
                query_db("insert into Admin (UUID, NAME, PASSWORDHASH) values (?, ?, ?);", (str(uuid.uuid4()), username, generate_password_hash(password)))
            except sqlite3.Error as e:
                logging.error(str(e.args[0]))
            print("Thank you, Admin has been added.")
            username = None
            password = None
        
        try:
            _NameNumber = query_db("select VALUE from Settings where NAME=?;", ('NameNumber',), one=True)    
            if _NameNumber is None:
                logging.error("Something went wrong with the settings.")
            else:
                if _NameNumber['VALUE'] == "true":
                    NameNumber = True
                else:
                    NameNumber = False
        except sqlite3.Error as e:
            logging.error(str(e.args[0]))
    app.run(host='127.0.0.1', port=8000)
    
    while True:
        pass