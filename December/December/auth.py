import hashlib
from . import settings
from .functions import get_option

def password_hash(password):
    md5 = hashlib.md5(settings.AUTH_SALT.encode('utf-8'))
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()

def auth_user(user, password):
    pswd = password_hash(password)
    if user != get_option("email") and user != get_option("username"):
        return False
    if pswd != get_option("password"):
        return False
    return True
