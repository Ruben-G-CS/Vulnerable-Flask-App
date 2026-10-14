from flask import Flask, request, render_template_string
import sqlite3 as sql

app = Flask(__name__)

def init_db():
    connection = sql.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    cursor.execute("DELETE FROM users")
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (None, "John", "Password123"))
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (None, "Jane", "Python123"))
    connection.commit()
    connection.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = sql.connect('users.db')
        cursor = connection.cursor()

        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
        cursor.execute(query)
        result = cursor.fetchone()

        connection.close()

        if result:
            message = 'Login has been successful, Welcome' + username
        else:
            message = 'You have entered incorrect details'

    return render_template_string('''
        <h2>Login</h2>
        <form method="POST">
            Username: <input type="text" name="username"><br><br>
            Password: <input type="password" name="password"><br><br>
            <input type="submit" value="Login">
        </form>
        <p>''' + message + '''</p>
    ''')

@app.route('/search')
def search():
    query = request.args.get('q','')

    return render_template_string('''
        <h2>Search</h2>
        <form method="GET">
            Search: <input type="text" name="q">
            <input type="submit" value="Search">
        </form>
        <h3>Results for: ''' + query + '''</h3>
    ''')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)