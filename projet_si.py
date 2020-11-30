#!/usr/bin/env python3
import rsa

pubkeys = dict() # name:key
privkeys = dict() # name:key
hashes = dict() # hash:plain message

def genkeys(who:str) :
    if who in pubkeys :
        return
    pub, priv = rsa.newkeys(1024)
    pubkeys[who] = pub
    privkeys[who] = priv

def sign(who:str, message:bytes) :
    privkey = privkeys[who]
    hsh = rsa.compute_hash(message, 'SHA-256')
    signed = rsa.sign_hash(hsh, privkey, 'SHA-256')
    hashes[hsh] = message
    return (hsh, signed)

def verify(who:str, signed:bytes, expected:bytes) :
    pubkey = pubkeys[who]
    hashfunc = None
    try :
        hashfunc = rsa.verify(expected, signed, pubkey)
    except rsa.VerificationError :
        return False
    else :
        hsh = rsa.compute_hash(expected, hashfunc)
        return hsh in hashes.keys()


if __name__ == "__main__":
    genkeys("Alice")
    genkeys("Bob")
    genkeys("Carl")
    hsh1, signed1 = sign("Alice", b"I gave Bob 2 apples")
    hsh2, signed2 = sign("Bob", hsh1+b"I gave Carl 1 apple")
    if not verify("Bob", signed2, hashes[hsh2]) :
        print("Chain not valid")
        exit()
    if not verify("Alice", signed1, hashes[hsh1]) :
        print("Chain not valide")
        exit()
    print("Chain valid")
