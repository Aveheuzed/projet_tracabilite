#!/usr/bin/env python3
import rsa
import pickle, pickletools

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
        self.oldmessages = tuple(__class__.from_signature(**rpz) for rpz in parents)

    def sign(self) :
        me = pickletools.optimize(pickle.dumps(self))
        privkey = Server().get_privkey(self.sender)
        hsh = rsa.compute_hash(me, __class__.HASHMETHOD)
        signature = rsa.sign_hash(hsh, privkey, __class__.HASHMETHOD)
        Server().register_message(hsh)
        return dict(plaintext=me, signature=signature, sender_id=self.sender)

    @staticmethod
    def from_signature(plaintext, signature, sender_id) :
        """Raises rsa.VerificationError if the message can't be authenticated."""
        # state is some yet-untrusted pickle dump; we can't load it until we've made sure it is safe
        # in general, pickle may be used for code injection, see the pickle docs for details

        hsh = rsa.compute_hash(plaintext, __class__.HASHMETHOD)

        if not Server().check_existence(hsh) :
            rsa.VerificationError(f"Message not found (hash : {hsh:8}...)")

        pubkey = Server().get_pubkey(sender_id)

        # may raise rsa.VerificationError
        hashfunc = rsa.verify(plaintext, signature, pubkey)
        if hashfunc != __class__.HASHMETHOD :
            raise rsa.VerificationError(f"Corrupted message : the hash function was {hashfunc}, versus {__class__.HASHMETHOD} expected")

        # only now is the message trustable
        return pickle.loads(plaintext)


class Server:

    __instance = None

    __userid = 0

    __slots__ = ("pubkeys", "_privkeys", "hashes", "bonds")

    def __new__(cls):
        # singleton
        if cls != __class__ :
            return object.__new__(cls)
        if cls.__instance is None :
            instance = object.__new__(cls)

            instance._privkeys = dict() # DEBUG only

            instance.pubkeys = dict() # user_id : pubkey
            instance.hashes = set() # plain hashes
            instance.bonds = dict() # message_id : Tuple[message_ids] (enfant → parents)

            cls.__instance = instance

        return cls.__instance

    def new_user(self)->dict :
        pub, priv = rsa.newkeys(1024)
        uid = __class__.__userid
        __class__.__userid += 1
        self.register_user(uid, pubkey=pub, privkey=priv)
        return dict(id=uid, pub=pub, priv=priv)

    def get_pubkey(self, user_id:int) :
        return self.pubkeys.get(user_id)

    def get_privkey(self, user_id:int) :
        """Not to be actually used; the private key is _private_, never to be shared → stored locally on the client's device"""
        return self._privkeys[user_id]

    def register_user(self, user_id:int, *, pubkey, privkey) :
        if user_id in self.pubkeys :
            if self.pubkeys[user_id] != pubkey :
                raise RuntimeError("A user with this id has already registered with a different key.")
        else :
            self.pubkeys[user_id] = pubkey
            self._privkeys[user_id] = privkey

    def register_message(self, hsh) :
        self.hashes.add(hsh)

    def check_existence(self, hsh) :
        """Returns True if the hash has been found to be registered."""
        return hsh in self.hashes

if __name__ == '__main__':
    s = Server()
    Alice = s.new_user()
    Bob = s.new_user()

    m1 = Message(Alice["id"], "J'ai donné 3 pommes à Bob.".encode())
    m2 = Message(Bob["id"], "J'ai mangé les trois pommes d'Alice".encode(), m1)

    authentication = m2.sign()

    del m1
    del m2

    restored = Message.from_signature(**authentication)

    print(restored.message.decode())
    print(restored.oldmessages[0].message.decode())
