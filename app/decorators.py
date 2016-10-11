from functools import wraps
from flask import abort
from flask_login import current_user

def member_required(fn):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.member:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator(fn)

def staff_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.staff \
               or not current_user.staff.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return staff_required(0xffff)(f)
