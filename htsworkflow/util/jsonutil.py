import json

_ENCODER_METHOD = 1
_WRITE_METHOD = 2

JSON_METHOD = None

try:
    json.write({})
except:
    JSON_METHOD = _ENCODER_METHOD

try:
    json.JSONEncoder()
except:
    JSON_METHOD = _WRITE_METHOD

assert JSON_METHOD is not None


def encode_json(data):
    """
    encodes json data given whatever json module we have access to (2.6 builtin or python-json)
    """
    if JSON_METHOD == _ENCODER_METHOD:
        j = json.JSONEncoder()
        return j.encode(data)
    
    elif JSON_METHOD == _WRITE_METHOD:
        return json.write(data)

    msg = "JSON_METHOD of value %s not supported." % (JSON_METHOD)
    raise ValueError, msg