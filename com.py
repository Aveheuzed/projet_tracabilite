from flask import Flask, request, jsonify, make_response
import MySQLdb
import time
from projet_si_poo import *
import rsa
import pickle, pickletools

from flask_cors import CORS


app = Flask(__name__)
CORS(app)


def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "phpmyadmin",
                            passwd = "foo",
                            db = "block_track")
    c = conn.cursor()

    return conn,c

"""API endpoints :
/create : create a new user=entity, returns its ID
/new_message/noparent : create a new message without parents, returns its hash
/getOldMessages : returns a JSON representation of an existing message, including its parents
/new_message/ : creates a new message with parents, passed as a POST array; returns the new message's hash
/entity/<int:id> : returns public details about an entity (user) in JSON"""

@app.route('/create',methods=['POST'])
def createUser():
    #-----------POST-FORM-------------------#
    name = request.form.get('name')
    address = request.form.get('address')
    desc = request.form.get('description')
    logo = request.form.get('logo')
    #-----------GEN-KEYS--------------------#
    pubkey, privkey = rsa.newkeys(1024)

    #-----------ENCODE-FOR-DB----------------#
    pubkey_n = pickle.dumps(pubkey).hex()
    privkey_n = pickle.dumps(privkey).hex()
    #-----------INSERT-IN-DB----------------#
    con, cur = connection()
    cur.execute(f"INSERT INTO `entities` (`name`, `public_key`, `private_key`,`description`, `address`, `logo`) VALUES ('{name}', '{pubkey_n}', '{privkey_n}','{desc}', '{address}', '{logo}')")
    con.commit()
    cur.close()

    #-----------RETURN-ID-------------------#
    con, cur = connection()
    cur.execute(f"SELECT `id_entity` FROM `entities` WHERE `name` = '{name}'")
    con.commit()
    data = cur.fetchall()
    cur.close()
    return jsonify(data[0][0])

@app.route('/new_message/noparent', methods=['POST'])
def newMessageNoParent():
    #-----------POST-FORM-------------------#
    sender_id = request.form.get('sender_id')
    msg = request.form.get('message')
    message = Message(sender_id, msg.encode())
    msghash = message.sign()
    return jsonify(msghash.hex())


@app.route('/getOldMessages',methods=['POST'])
def getOldMessages():
    hsh = request.form.get('hash')
    hsh = bytes.fromhex(hsh)
    old_messages = Message.from_signature(hsh)
    #-----------CONSTRUCT-NICE-JSON----------#
    return old_messages.json_encode()


@app.route('/new_message/', methods=['POST'])
def newMessage():
    sender_id = request.form.get('sender_id')
    msg = request.form.get('message') ; print(type(request.form.get("hash")))
    hsh = [Message.from_signature(bytes.fromhex(hsh)) for hsh in eval(request.form.get('hash'))]
    print(hsh)
    message = Message(sender_id, msg.encode(), *hsh)
    message_hash = message.sign()
    return jsonify(message_hash.hex())


@app.route('/entity/<int:id>', methods=["GET", "POST"])
def get(id):
    con, cur = connection()
    cur.execute(f"SELECT id_entity, name, public_key, description, address, logo FROM `entities` WHERE `id_entity` = {id}")
    con.commit()
    data = cur.fetchall()
    cur.close()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
