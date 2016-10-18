from django.conf.urls import url

from .views import LazyRegisterView

urlpatterns = [
    url(r'^$', LazyRegisterView.as_view(), name='rest_lazyregister'),
]
