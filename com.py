from flask import Flask, request, jsonify, make_response
import MySQLdb
import time
from projet_si_poo import *
import rsa
import pickle, pickletools
import base64

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
        pubkey_n = base64.b64encode(pubkey_n).decode('utf-8')

        #-----------INSERT-IN-DB----------------#
        con, cur = connection()
        cur.execute(f"INSERT INTO `entities` (`name`, `public_key`, `description`, `address`, `logo`) VALUES ('{name}', '{pubkey_n}', '{desc}', '{address}', '{logo}')")
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
	return jsonify(msghash)
    except Exception as e:
        return repr(e) #'failure'


@app.route('/getOldMessages',methods=['POST'])
def getOldMessages():
    try :
        hsh = request.form.get('hash')
        old_messages = Message.from_signature(hsh)
        #-----------CONSTRUCT-NICE-JSON----------#
        return jsonify(old_messages.json_encode())
    except Exception as e:
        return repr(e) #'failure'

@app.route('/new_message/', methods=['POST'])
def newMessage():
    try :
        sender_id = request.form.get('sender_id')
        msg = request.form.get('message')
        hsh = request.form.get('hash')
    
        message = Message(sender_id, msg.encode(), Message.from_signature(hsh))
        message_hash = message.sign()
    except Exception as e:
        return repr(e) #'failure'

if __name__ == "__main__":
    app.run(debug=True, port=5000)
