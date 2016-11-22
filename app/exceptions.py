class ValidationError(ValueError):
    pass

# Weixin access token got error
class AccessTokenGotError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.msg = message

    def __str__(self):
        return '{"errcode": %s, "errmsg": "%s"}' % (self.code, self.message)

# Weixin Pay  error
class PayError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.msg = message

    def __str__(self):
        return '{"errcode": %s, "errmsg": "%s"}' % (self.code, self.message)
