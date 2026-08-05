from functools import wraps

from flask import abort
from flask_login import current_user


def roles_requeridos(*roles_permitidos):
    """Restringe una vista a los usuarios que tengan alguno de los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.tiene_rol(*roles_permitidos):
                abort(403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador
