from django.conf import settings

# Lazy user timeout in seconds - defaults to two weeks
LAZY_USER_TIMEOUT = getattr(settings, 'REST_AUTH_LAZY_USER_TIMEOUT', 1209600)
