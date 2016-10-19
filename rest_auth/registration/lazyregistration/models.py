import re
import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import now
import six

from rest_auth.registration.lazyregistration.utils import is_lazy_user
from rest_auth.registration.lazyregistration.exceptions import NotLazyError
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

    def _get_all_related_objects(self, user):
        return [
            f for f in user._meta.get_fields()
            # if (f.one_to_many or f.one_to_one)
            if f.one_to_many
            and f.auto_created and not f.concrete
        ]

    def _redirect_all_related_objects(self, lazy_user, new_user):
        # Get all field names that represent related objects
        field_names = [field.get_accessor_name() for field in self._get_all_related_objects(lazy_user)]

        # For each field, add the related objects to the new user
        for field_name in field_names:
            # Get the object\related manager from the field
            objOrMgr = getattr(lazy_user, field_name)

            if objOrMgr.__class__.__name__ == 'RelatedManager':
                # In case the relation is one-to-many or many-to-many, we have to deal with the 'relatd manager'.

                # Get the new user's related manager of that field
                newObjMgr = getattr(new_user, field_name)

                # Add the old user's objects from that field to the new user
                newObjMgr.add(*list(objOrMgr.all()), bulk=False)
            else:
                # The relation is one-to-one. Just transfer the object to the new user.
                setattr(new_user, field_name, objOrMgr)

        # Save changes to the database
        new_user.save()

    def convert(self, lazy_user, new_user):
        """ Convert a lazy user to a non-lazy one.
        A conversion is basically moving all the related objects of the user to a new user
        provided from outside.

        The converted ``User`` object is returned.

        Raises a LazyError if the user is not lazy.
        """
        if not is_lazy_user(lazy_user):
            raise NotLazyError('You cannot convert a non-lazy user')

        self._redirect_all_related_objects(lazy_user, new_user)

        # We need to remove the unecessary lazy-user
        lazy_user.delete()
        converted.send(self, user=new_user)
        return new_user

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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='lazy')
    created = models.DateTimeField(default=now, db_index=True)
    objects = LazyUserManager()

    @classmethod
    def get_user_class(cls):
        return cls._meta.get_field('user').rel.to

    def __str__(self):
        return '{0}:{1}'.format(self.user, self.created)
