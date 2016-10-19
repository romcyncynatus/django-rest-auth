from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.generics import GenericAPIView
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework import serializers

from allauth.account.adapter import get_adapter
from allauth.account.views import ConfirmEmailView
from allauth.account.utils import complete_signup
from allauth.account import app_settings as allauth_settings

from rest_auth.app_settings import (TokenSerializer,
                                    JWTSerializer,
                                    create_token)
from rest_auth.registration.serializers import (SocialLoginSerializer,
                                                VerifyEmailSerializer)
from rest_auth.views import LoginView
from rest_auth.registration.views import RegisterView
from rest_auth.models import TokenModel

from rest_auth.utils import jwt_encode

# Lazy registration
from rest_auth.registration.lazyregistration.models import LazyUser
from rest_auth.registration.lazyregistration.permissions import IsLazyUser

class LazyUserCreateView(CreateAPIView):
    serializer_class = serializers.Serializer
    permission_classes = (AllowAny,)
    token_model = TokenModel

    def create(self, request, *args, **kwargs):
        # Create a lazy user
        user, username = LazyUser.objects.create_lazy_user()
        
        # Create a token
        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(user)
        else:
            create_token(self.token_model, user, None)

        # Complete it's signup without a confirmation email
        complete_signup(self.request._request, user, None, None)

        return Response(self.get_response_data(user), status=status.HTTP_201_CREATED)
        
    def get_response_data(self, user):
        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': user,
                'token': self.token
            }
            return JWTSerializer(data).data
        else:
            return TokenSerializer(user.auth_token).data


class LazyUserLoginView(LoginView):
    permission_classes = (IsLazyUser,)

    def __init__(self):
        super(LazyUserLoginView, self).__init__()

        self.lazy_user = None
        self.user = None

    def post(self, request, *args, **kwargs):
        # Store the lazy user
        self.lazy_user = request.user

        # Call original post function (after which self.user should be populated)
        response = super(LazyUserLoginView, self).post(request, *args, **kwargs)

        # Now we should have both the request (lazy) user and the newly created user,
        # so we can convert our lazy user.
        LazyUser.objects.convert(self.lazy_user, self.user)

        return response


class LazyUserRegisterView(RegisterView):
    permission_classes = (IsLazyUser,)

    def __init__(self):
        super(LazyUserRegisterView, self).__init__()

        self.lazy_user = None
        self.user = None

    def create(self, request, *args, **kwargs):
        # Store the lazy user
        self.lazy_user = request.user

        # Call original create function
        return super(LazyUserRegisterView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Call the original perform_create (after which the new user will get created)
        self.user = super(LazyUserRegisterView, self).perform_create(serializer)

        # Now we should have both the request (lazy) user and the newly created user,
        # so we can convert our lazy user.
        LazyUser.objects.convert(self.lazy_user, self.user)

        return self.user