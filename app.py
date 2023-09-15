from flask import Flask, render_template, request, url_for, flash, session, redirect
from flask_mysqldb import MySQL
from flask_dance.contrib.github import make_github_blueprint, github
from flask import jsonify
import MySQLdb.cursors
import re
app = Flask(__name__)
app.secret_key = 'abcdefqwerty'

github_blueprint = make_github_blueprint(client_id='fdc37dee82b6ea3f0b8e', client_secret = '505317e0d068680eb8c467e3ae299494aa053dba')
app.register_blueprint(github_blueprint, url_prefix='/github_login')
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'itd105app'

mysql = MySQL(app)

@app.route('/github')
def github_login():
    if not github.authorized:
        return redirect(url_for('github.login'))
    else:
        account_info = github.get('/user')
        if account_info.ok:
            session['loggedin'] = True   # set the session variable
            return redirect(url_for('index'))
    return '<h1>Request Failed</h1>'

@app.route('/')
@app.route('/login', methods = ['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['id']
            session['email'] = user['email']
            message = 'logged in successful'
            return redirect(url_for('index')) # Redirect to index after successful login
        else:
            message = 'Please enter correct creds'
    return render_template('login.html', message=message)


@app.route('/index')
def index():
    if not (github.authorized or ('loggedin' in session and session['loggedin'])):
        flash('You need to login first!')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM globaltemps ORDER BY date DESC')
    data = cursor.fetchall()
    print(data)
    return render_template('index.html', data=data)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.pop('loggedin', None)
        session.pop('userid', None)
        session.pop('email', None)
        return redirect(url_for('login'))
    # Handle GET request (if needed)
    return render_template('login.html')  # Replace 'logout.html' with your template

# You can also keep your existing logout route for POST requests if needed.



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'fname' in request.form and 'lname' in request.form:
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO users (`first_name`, `last_name`, `email`, `password`) VALUES (%s, %s, %s, %s)", 
                       (fname, lname, email, password))

        mysql.connection.commit()
        cursor.close()  # Remember to call the close method using ()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/submit_data', methods=['POST'])
def submit_data():
    if request.method == 'POST' and 'date' in request.form and 'lave' in request.form and 'lmax' in request.form and 'lmin' in request.form:
        date = request.form['date']
        lave = request.form['lave']
        lmax = request.form['lmax']
        lmin = request.form['lmin']

        # Now, you can insert this data into your 'globaltemps' table.
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO globaltemps (date, LandAverageTemperature, LandMaxTemperature, LandMinTemperature) VALUES (%s, %s, %s, %s)', (date, lave, lmax, lmin))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('index'))

    return jsonify({"error": "Invalid request method."})

@app.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    if not (github.authorized or ('loggedin' in session and session['loggedin'])):
        flash('You need to login first!')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM globaltemps WHERE id = %s', (record_id,))
    mysql.connection.commit()
    cursor.close()

    # Return a JSON response indicating success
    return jsonify({"message": "Record deleted successfully"})

@app.route('/get_record/<int:record_id>', methods=['GET'])
def get_record(record_id):
    if not (github.authorized or ('loggedin' in session and session['loggedin'])):
        flash('You need to login first!')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM globaltemps WHERE id = %s', (record_id,))
    record_data = cursor.fetchone()
    cursor.close()

    # Return the record data as JSON
    return jsonify(record_data)

@app.route('/edit_record', methods=['POST'])
def edit_record():
    if not (github.authorized or ('loggedin' in session and session['loggedin'])):
        flash('You need to login first!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        record_id = request.form['record_id']
        date = request.form['edtdate']
        lave = request.form['edtlave']
        lmax = request.form['edtlmax']
        lmin = request.form['edtlmin']

        # Update the record in the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE globaltemps SET date = %s, LandAverageTemperature = %s, LandMaxTemperature = %s, LandMinTemperature = %s WHERE id = %s",
                       (date, lave, lmax, lmin, record_id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('index'))

    return jsonify({"error": "Invalid request method."})

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    if not (github.authorized or ('loggedin' in session and session['loggedin'])):
        flash('You need to login first!')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT date, LandAverageTemperature, LandMaxTemperature, LandMinTemperature FROM globaltemps')
    chart_data = cursor.fetchall()
    cursor.close()

    # Return the data as JSON
    return jsonify(chart_data)



