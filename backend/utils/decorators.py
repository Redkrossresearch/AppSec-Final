from functools import wraps

from flask import jsonify
from flask_login import current_user


def owns_resource(get_owner_id):
    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            if get_owner_id(*args, **kwargs) != current_user.id:
                return jsonify({"error": "Forbidden"}), 403
            return function(*args, **kwargs)

        return wrapped

    return decorator
