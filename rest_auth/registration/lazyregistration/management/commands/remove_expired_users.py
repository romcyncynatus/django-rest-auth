from django.utils import timezone
from django.conf import settings

from django.core.management.base import BaseCommand

from rest_auth.registration.lazyregistration.app_settings import LAZY_USER_TIMEOUT
from rest_auth.registration.lazyregistration.models import LazyUser


class Command(BaseCommand):
    help = u"""Remove all users whose sessions have expired and who haven't
               set a password. This assumes you are using database sessions"""

    def handle(self, **options):
        # Delete each of these users. We don't use the queryset delete()
        # because we want cascades to work (including, of course, the LazyUser
        # object itself)
        old_users = self.to_delete()
        count = old_users.count()
        for lazy_user in old_users:
            lazy_user.user.delete()
            
        self.stdout.write(self.style.SUCCESS("{0} Lazy Users deleted.".format(count)))

    def to_delete(self):
        delete_before = timezone.now() - timezone.timedelta(seconds=LAZY_USER_TIMEOUT)
        
        return LazyUser.objects.filter(
            user__last_login__lt=delete_before
        ).select_related('user')
