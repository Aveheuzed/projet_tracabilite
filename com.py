from flask import Flask, request, jsonify, make_response
from flask_mysqldb import MySQL

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
    mysql.connection.commit()

'''

@app.route('/', methods=['POST','GET'])
def index():
    if request.method = "POST":
        return "POST"
    else:
        return "GET"
    return 200
  
if __name__ == "__main__":
    app.run(debug=True, port=5000)