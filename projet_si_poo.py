#!/usr/bin/env python3
import rsa
import pickle, pickletools
import json

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

        message = Server.get_message(hsh)
        sender_id = message["sender_id"]
        signature = message["signature"]
        plaintext = message["plaintext"]
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

    __messages = dict()
    __entities = dict()

    @classmethod
    def get_pubkey(cls, user_id:int)->rsa.PublicKey :
        return cls.__entities.get(user_id)["pubkey"]

    @classmethod
    def get_privkey(cls, user_id:int)->rsa.PrivateKey :
        return cls.__entities.get(user_id)["privkey"]

    @classmethod
    def register_user(cls, nom:str, adresse:str, logo:str, *, pubkey:rsa.PublicKey, privkey:rsa.PrivateKey)->int :
        uid = len(cls.__entities)
        cls.__entities[uid] = dict(
                                nom=nom,
                                adresse=adresse,
                                logo=logo,
                                pubkey=pubkey,
                                privkey=privkey
                                )
        return uid

    @classmethod
    def register_message(cls, hsh:bytes, plaintext:bytes, signature:bytes, sender_id:int)->None :
        cls.__messages[hsh] = dict(
                                plaintext=plaintext,
                                signature=signature,
                                sender_id=sender_id
                                )
    @classmethod
    def get_message(cls, hsh:bytes)->dict :
        """Raises KeyError is hash not found."""
        return cls.__messages[hsh]


def new_user(nom="", adresse="", logo="")->int :
    """Generates keys and all, return the new user's id"""
    pub, priv = rsa.newkeys(1024)
    return Server.register_user(nom, adresse, logo, pubkey=pub, privkey=priv)



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
