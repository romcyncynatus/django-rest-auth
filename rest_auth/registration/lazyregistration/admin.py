from django.utils import timezone
from django.contrib import admin
from .models import LazyUser
from .app_settings import LAZY_USER_TIMEOUT


@admin.register(LazyUser)
class LazyUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'created',)
    actions = ('cleanup_lazyusers',)

    def cleanup_lazyusers(self, request, queryset):
        delete_before = timezone.now() - timezone.timedelta(seconds=LAZY_USER_TIMEOUT)
        old_users = queryset.filter(user__last_login__lt=delete_before)
        count = old_users.count()

        for lazy_user in old_users:
            # iterate so any .delete() methods get called and signals are sent
            lazy_user.user.delete()

        self.message_user(request, "{0} Lazy Users deleted." .format(count))

    cleanup_lazyusers.short_description = (
        'Delete selected lazy users and unconverted users older than {}'.format(
            timezone.timedelta(seconds=LAZY_USER_TIMEOUT))
    )
