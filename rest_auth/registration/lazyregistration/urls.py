from django.conf.urls import url

from rest_auth.registration.lazyregistration.views import (LazyUserCreateView,
                                                           LazyUserLoginView,
                                                           LazyUserRegisterView)

urlpatterns = [
    url(r'^create/$', LazyUserCreateView.as_view(), name='rest_auth_lazyregisteration_create'),
    url(r'^login/$', LazyUserLoginView.as_view(), name='rest_auth_lazyregisteration_login'),
    url(r'^register/$', LazyUserRegisterView.as_view(), name='rest_auth_lazyregisteration_register'),
]
