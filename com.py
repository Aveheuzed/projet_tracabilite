from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields

'''
    Flask: web app
    request: requests
    jsonify: JSON output -> response obj with mime type of app
    SQLalchemy: access db
    marshmallow: serialize objects
'''
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://<mysql_username>:<mysql_password>@<mysql_host>:<mysql_port>/<mysql_db>'
db = SQLAlchemy(app)


@app.route('/', methods=['POST'])

  
if __name__ == "__main__":
    app.run(debug=True, port=5000)