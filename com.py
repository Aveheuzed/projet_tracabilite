import sys
from flask import Flask, request, jsonify, make_response
import MySQLdb
import time
from projet_si_poo import *
import rsa
import pickle, pickletools
import base64

from flask_cors import CORS


def bytesToStr(bytesIn):
        bytesIn = base64.b64encode(bytesIn).decode('utf-8')
        return bytesIn

def StrToBytes(strIn):
        strIn = base64.b64decode(bytes(strIn,'utf-8'))
        return strIn


app = Flask(__name__)
CORS(app)
def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "phpmyadmin",
                            passwd = "foo",
                            db = "block_track")
    c = conn.cursor()

    return conn,c

@app.route('/create',methods=['POST'])
def createUser():
    try:
        #-----------POST-FORM-------------------#
        name = request.form.get('name')
        address = request.form.get('address')
        desc = request.form.get('description')
        logo = request.form.get('logo')
        #-----------GEN-KEYS--------------------#
        pubkey, privkey = rsa.newkeys(1024)

        #-----------ENCODE-FOR-DB----------------#
        pubkey_n = pickle.dumps(pubkey)
        pubkey_n = base64.b64encode(pubkey_n).decode('utf-8') ; privkey_n = pickle.dumps(privkey) ; privkey_n = base64.b64encode(privkey_n).decode('utf-8')
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
    except Exception as e:
        return repr(e) #'failure'

@app.route('/new_message/noparent', methods=['POST'])
def newMessageNoParent():
    try :
        #-----------POST-FORM-------------------#
        sender_id = request.form.get('sender_id')
        msg = request.form.get('message')
        message = Message(sender_id, msg.encode())
        msghash = message.sign()
        return jsonify(bytesToStr(msghash))
    except Exception as e:
        return repr(e) #'failure'


@app.route('/getOldMessages',methods=['POST'])
def getOldMessages():
    try :
        hsh = request.form.get('hash')
        hsh = StrToBytes(hsh)
        old_messages = Message.from_signature(hsh)
        #-----------CONSTRUCT-NICE-JSON----------#
        return old_messages.json_encode()
    except Exception as e:
        raise e
        return repr(e) #'failure'

@app.route('/new_message/', methods=['POST'])
def newMessage():
    try :
        sender_id = request.form.get('sender_id')
        msg = request.form.get('message') ; print(type(request.form.get("hash")))
        hsh = [Message.from_signature(StrToBytes(hsh)) for hsh in eval(request.form.get('hash'))]
        print(hsh)
        message = Message(sender_id, msg.encode(), *hsh)
        message_hash = message.sign()
        return jsonify(bytesToStr(message_hash))
    except Exception as e:
        raise e
        return repr(e) #'failure'

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
