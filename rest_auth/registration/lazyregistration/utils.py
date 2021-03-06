def is_lazy_user(user):
    """ Return True if the passed user is a lazy user. """
    # Anonymous users are not lazy.
    if user.is_anonymous():
        return False

    # Check the user backend. If the lazy signup backend
    # authenticated them, then the user is lazy.
    backend = getattr(user, 'backend', None)
    if backend == 'rest_auth.registration.lazyregistration.backends.LazySignupBackend':
        return True

    # Otherwise, we have to fall back to checking the database.
    from rest_auth.registration.lazyregistration.models import LazyUser
    return bool(LazyUser.objects.filter(user=user).count() > 0)
