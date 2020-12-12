#!/usr/bin/env python3
import rsa
import pickle, pickletools

def connection():
    conn = MySQLdb.connect(host="localhost",
                            user = "root",
                            passwd = "",
                            db = "block_track")
    c = conn.cursor()
    
    return conn,c

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

        con, cur = connection()
        cur.execute(f"SELECT * FROM `messages` WHERE `hsh` = {hsh}")
        con.commit()
        message = cur.fetchall()
        cur.close()

        sender_id = message[1]
        signature = message[2]
        plaintext = message[3]
        # plaintext is some yet-untrusted pickle dump; we can't load it until we've made sure it is safe
        # in general, pickle may be used for code injection, see the pickle docs for details

        pubkey = Server.get_pubkey(sender_id)

        # may raise rsa.VerificationError
        hashfunc = rsa.verify(plaintext, signature, pubkey)
        if hashfunc != __class__.HASHMETHOD :
            raise rsa.VerificationError(f"Corrupted message : the hash function was {hashfunc}, versus {__class__.HASHMETHOD} expected")

        # only now is the message trustable
        return pickle.loads(plaintext)


class Server:

    __slots__ = ()

    @classmethod
    def get_pubkey(cls, user_id:int)->rsa.PublicKey :
        con, cur = connection()
        cur.execute(f"SELECT public_key FROM entity WHERE `id_entity` = {user_id}")
        data = cur.fetchall()
        #-----------PICKLE-LOADS----------------#

        cur.close()
        return data

    @classmethod
    def get_privkey(cls, user_id:int)->rsa.PrivateKey :
        return cls.__entities.get(user_id)["privkey"]

    @classmethod
    def register_message(cls, hsh:bytes, plaintext:bytes, signature:bytes, sender_id:int)->None :
        con, cur = connection()
        cur.execute(f"INSERT INTO `messages` (`hsh`, `plaintext`, `signature`, `sender_id`) VALUES ({hsh}, {plaintext}, {signature}, {sender_id})")
        con.commit()
        cur.close()

__all__ = ("new_user", "Message")

if __name__ == '__main__':
    Alice = new_user()
    Bob = new_user()

    ## transaction

    # premier message sans parent
    m1 = Message(Alice, "J'ai donné 3 pommes à Bob.".encode())
    auth1 = m1.sign() ; del m1

    # auth1 passe dans le monde réel :)

    m2 = Message(Bob, "J'ai mangé les trois pommes d'Alice".encode(), Message.from_signature(auth1))
    auth2 = m2.sign() ; del m2

    # auth2 passe dans le monde réel :)
    restored = Message.from_signature(auth2)

    print(restored.message.decode()) # texte du dernier message
    print(restored.oldmessages[0].message.decode()) # accès au(x) parent(s)
