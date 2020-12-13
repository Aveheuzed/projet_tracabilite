#!/usr/bin/env python3
import rsa
import pickle, pickletools
import json
import MySQLdb
import base64

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "root",
                            passwd = "",
                            db = "block_track")
    c = conn.cursor()

    return conn,c

def bytesToStr(bytesIn):
    bytesIn = base64.b64encode(bytesIn).decode('utf-8')
    return bytesIn

def StrToBytes(strIn):
    strIn = base64.b64decode(bytes(strIn,'utf-8'))
    return strIn

class Message:

    __slots__ = ("sender", "message", "oldmessages")

    HASHMETHOD = 'SHA-512'

    def __init__(self, sender_id:int, message:bytes, *parents):

        self.sender = sender_id
        self.message = message
        self.oldmessages = parents

    def __getstate__(self) :
        return (self.sender, self.message, *(msg.sign() for msg in self.oldmessages))

    def __setstate__(self, state) :
        self.sender, self.message, *parents = state
        self.oldmessages = tuple(__class__.from_signature(hsh) for hsh in parents)

    def sign(self)->bytes :
        me = pickletools.optimize(pickle.dumps(self))
        privkey = Server.get_privkey(self.sender)
        hsh = rsa.compute_hash(me, __class__.HASHMETHOD)
        signature = rsa.sign_hash(hsh, privkey, __class__.HASHMETHOD)
        Server.register_message(hsh, me, signature, self.sender)
        return hsh

    @staticmethod
    def from_signature(hsh:bytes) :
        """Raises rsa.VerificationError if the message can't be authenticated.
        Raises KeyError (from Server.get_message) if the message can't be found."""
        hsh = bytesToStr(hsh)
        con, cur = connection()
        cur.execute(f"SELECT * FROM `messages` WHERE `hsh` = '{hsh}'")
        con.commit()
        data = cur.fetchall()
        cur.close()
        hsh = StrToBytes(hsh)

        sender_id = data[0][3]
        signature = data[0][2]
        plaintext = data[0][1]

        signature = StrToBytes(signature)
        plaintext = StrToBytes(plaintext)
        # plaintext is some yet-untrusted pickle dump; we can't load it until we've made sure it is safe
        # in general, pickle may be used for code injection, see the pickle docs for details

        pubkey = Server.get_pubkey(sender_id)

        # may raise rsa.VerificationError
        hashfunc = rsa.verify(plaintext, signature, pubkey)
        if hashfunc != __class__.HASHMETHOD :
            raise rsa.VerificationError(f"Corrupted message : the hash function was {hashfunc}, versus {__class__.HASHMETHOD} expected")

        # only now is the message trustable
        return pickle.loads(plaintext)

    def json_encode(self):
        return JsonMessageEncoder().encode(self)



class JsonMessageEncoder(json.JSONEncoder) :

    def default(self, obj) :
        if not isinstance(obj, Message) :
            return super().default(obj)
        return dict(
                    user_id=obj.sender,
                    message=obj.message.decode(errors="replace"),
                    children=obj.oldmessages
                    )



class Server:

    __slots__ = ()

    @classmethod
    def get_pubkey(cls, user_id:int)->rsa.PublicKey :
        con, cur = connection()
        cur.execute(f"SELECT * FROM entity WHERE `id_entity` = {user_id}")
        data = cur.fetchall()
        pubkey = pickle.loads(base64.b64decode(bytes(data[0][5], 'utf-8')))
        cur.close()
        return pubkey

    @classmethod
    def get_privkey(cls, user_id:int)->rsa.PrivateKey :
        con, cur = connection()
        cur.execute(f"SELECT * FROM entity WHERE `id_entity` = {user_id}")
        data = cur.fetchall()
        privkey = pickle.loads(base64.b64decode(bytes(data[0][6], 'utf-8')))
        cur.close()
        return privkey

    @classmethod
    def register_message(cls, hsh:bytes, plaintext:bytes, signature:bytes, sender_id:int)->None :
        con, cur = connection()
        hsh = bytesToStr(hsh)
        plaintext = bytesToStr(plaintext)
        signature = bytesToStr(signature)
        cur.execute(f"INSERT INTO `messages` (`hsh`, `plaintext`, `signature`, `sender_id`) VALUES ('{hsh}', '{plaintext}', '{signature}', {sender_id})")
        con.commit()
        cur.close()

__all__ = ("new_user", "Message")

if __name__ == '__main__':

    #print(Server.get_pubkey(62))
    #print(Server.get_privkey(62))

    message = Message(62, "Hello There".encode())
    msghash1 = message.sign()
    #print(Message.from_signature(msghash).message.decode())

    m2 = Message(62,"Iam 3".encode(),Message.from_signature(msghash1))
    m2hash = m2.sign()

    res = Message.from_signature(m2hash)

    print(res.message.decode())
    print(res.oldmessages[0].message.decode())
