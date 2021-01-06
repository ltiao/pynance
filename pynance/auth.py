import hmac, 
from hashlib import sha256
from urllib.parse import urlencode

def create_hmac(params, secret_key, digestmod=sha256):
    return hmac.new(secret_key.encode("utf-8"),
                    msg=urlencode(params).encode("utf-8"),
                    digestmod=digestmod)

def create_signature(params, secret_key, digestmod=sha256):
    return create_hmac(params, secret_key).hexdigest()

def create_params(params, secret_key):

    assert "signature" not in params, \
        "key `signature` must not be contained in params dict!"
    signature = create_signature(params, secret_key)

    params_new = dict(params) # deep-copy
    params_new["signature"] = signature

    return params_new
