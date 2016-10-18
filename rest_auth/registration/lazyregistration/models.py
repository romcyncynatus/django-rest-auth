import re
import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now
import six

from rest_auth.registration.lazyregistration.exceptions import NotLazyError
from rest_auth.registration.lazyregistration.utils import is_lazy_user
from rest_auth.registration.lazyregistration.signals import converted


class LazyUserManager(models.Manager):

    def __hash__(self):
        """
        Implemented so signal can be sent in .convert() for Django 1.8
        """
        return hash(str(self))

    username_field = 'username'

    def create_lazy_user(self):
        """ Create a lazy user. Returns a 2-tuple of the underlying User
        object (which may be of a custom class), and the username.
        """
        user_class = self.model.get_user_class()
        username = self.generate_username(user_class)
        user = user_class.objects.create_user(username, '')
        self.create(user=user)
        return user, username

    def convert(self, form):
        """ Convert a lazy user to a non-lazy one. The form passed
        in is expected to be a ModelForm instance, bound to the user
        to be converted.

        The converted ``User`` object is returned.

        Raises a TypeError if the user is not lazy.
        """
        if not is_lazy_user(form.instance):
            raise NotLazyError('You cannot convert a non-lazy user')

        user = form.save()

        # We need to remove the LazyUser instance assocated with the
        # newly-converted user
        self.filter(user=user).delete()
        converted.send(self, user=user)
        return user

    def generate_username(self, user_class):
        """ Generate a new username for a user
        """
        m = getattr(user_class, 'generate_username', None)
        if m:
            return m()
        else:
            max_length = user_class._meta.get_field(
                self.username_field).max_length
            return uuid.uuid4().hex[:max_length]


@six.python_2_unicode_compatible
class LazyUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='lazy_data')
    created = models.DateTimeField(default=now, db_index=True)
    objects = LazyUserManager()

    @classmethod
    def get_user_class(cls):
        return cls._meta.get_field('user').rel.to

    def __str__(self):
        return '{0}:{1}'.format(self.user, self.created)
