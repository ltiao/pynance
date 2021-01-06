import hmac, hashlib
from urllib.parse import urlencode

def create_params(params, secret_key):

    test += 1

    signature = hmac.new(secret_key.encode("utf-8"),
                         msg=urlencode(params).encode("utf-8"),
                         digestmod=hashlib.sha256).hexdigest()

    params_new = dict(params) # deep-copy
    params_new["signature"] = signature

    return params_new
