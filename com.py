from flask import Flask, request, jsonify, make_response
from flask_mysqldb import MySQL
import time
import projet_si

'''
    Flask: web app
    request: requests
    jsonify: JSON output -> response obj with mime type of app
'''

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'MyDB'

mysql = MySQL(app)

''' 
    mysql.connection.cursor()
        .execute(query)
        .close()
        .fetchall()
        .fetchmany(size=1)
    mysql.connection.commit()

'''

@app.route('/', methods=['POST','GET'])
def index():
    return 200

@app.route('/time')
def get_current_time():
    return jsonify(time.time())

@app.route('/task/add', methods=['GET', 'POST'])
def add():
    ''' 
        Get input details
        if info in form
            -> d = request.form
               data = d['key']
    ''' 
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO  VALUES ",)
        mysql.connection.commit()
        cur.close()
        return 'success'
    except:
        return 'failure'

if __name__ == "__main__":
    app.run(debug=True, port=5000)