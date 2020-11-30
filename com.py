from flask import Flask, request, jsonify, make_response
import MySQLdb
import time
import projet_si


'''
    Flask: web app
    request: requests
    jsonify: JSON output -> response obj with mime type of app
'''

app = Flask(__name__)

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "phpmyadmin",
                            passwd = "foo",
                            db = "block_track")
    c = conn.cursor()
    return conn,c

@app.route('/', methods=['POST','GET'])
def index():
    return 200

@app.route('/dump')
def dump():
    con, cur = connection()
    cur.execute("SELECT * FROM entities")
    con.commit()
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

@app.route('/time')
def get_current_time():
    return jsonify(time.time())

@app.route('/entity/<int:id>', methods=['GET', 'POST'])
def entity_id(id):
    try:
        con, cur = connection()
        cur.execute(f"SELECT * FROM entities WHERE `id_entity` = {val}")
        con.commit()
        data = cur.fetchall()
        cur.close()
        return jsonify(data)
    except:
        return 'failure'

@app.route('/<string:id_hash>', methods=['GET', 'POST'])
def hash_id(id_hash):
    try:
        con, cur = connection()
        cur.execute("SELECT * FROM hashs")
        con.commit()
        data = cur.fetchall()
        cur.close()
        return jsonify(data)
    except:
        return 'failure'

if __name__ == "__main__":
    app.run(debug=True, port=5000)