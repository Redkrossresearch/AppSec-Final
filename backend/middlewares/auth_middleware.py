from flask_login import current_user


def current_identity():
    return current_user.to_dict() if current_user.is_authenticated else None
