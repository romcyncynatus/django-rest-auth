from rest_framework import permissions
from rest_auth.registration.lazyregistration.utils import is_lazy_user


class IsLazyUser(permissions.BasePermission):
    """
    Grant access to lazy users only.
    """
    def has_permission(self, request, view):
        return is_lazy_user(request.user)
        
class IsNotLazyUser(permissions.BasePermission):
    """
    Grant access to not-lazy users only.
    """
    def has_permission(self, request, view):
        return not is_lazy_user(request.user)
