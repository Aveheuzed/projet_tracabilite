from flask import Flask, request, jsonify, make_response
import MySQLdb
import time
import projet_si_poo
import rsa
import pickle, pickletools
import base64

app = Flask(__name__)

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "root",
                            passwd = "",
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
        cur.execute(f"INSERT INTO `entity` (`id_entity`, `name`, `public_key`, `description`, `address`, `logo`) VALUES (NULL, {name}, '{pubkey_n}', {desc}, {address}, {logo})")
        con.commit()
        cur.close()

        #-----------RETURN-ID-------------------#
        con, cur = connection()
        cur.execute(f"SELECT `id_entity` FROM `entity` WHERE `name` = {name}")
        con.commit()
        data = cur.fetchall()
        cur.close()
        return jsonify(data[0][0])
    except:
        return 'failure'

@app.route('/new_message/noparent', methods=['POST'])
def newMessageNoParent():
    #-----------POST-FORM-------------------#
    sender_id = request.form.get('sender_id')
    msg = request.form.get('message')

    message = Message(sender_id, msg.encode())
    msghash = message.sign()

@app.route('/getOldMessages',methods=['POST'])
def getOldMessages():
    hsh = request.form.get('hash')
    old_messages = Message.from_signature(hsh)
    #-----------CONSTRUCT-NICE-JSON----------#
    return jsonify(old_messages)

@app.route('/new_message/', methods=['POST'])
def newMessage():
    sender_id = request.form.get('sender_id')
    msg = request.form.get('message')
    hsh = request.form.get('hash')

    message = Message(sender_id, msg.encode(), Message.from_signature(hsh))
    message_hash = message.sign()

if __name__ == "__main__":
    app.run(debug=True, port=5000)