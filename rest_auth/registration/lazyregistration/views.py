from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework import serializers

from allauth.account.adapter import get_adapter
from allauth.account.views import ConfirmEmailView
from allauth.account.utils import complete_signup
from allauth.account import app_settings as allauth_settings

from rest_auth.app_settings import (TokenSerializer,
                                    UserTokenSerializer,
                                    JWTSerializer,
                                    create_token)
from rest_auth.registration.serializers import (SocialLoginSerializer,
                                                VerifyEmailSerializer)
from rest_auth.views import LoginView
from rest_auth.models import TokenModel
from .app_settings import RegisterSerializer

from rest_auth.utils import jwt_encode

# Lazy signup
from rest_auth.registration.lazyregistration.models import LazyUser

class LazyRegisterView(CreateAPIView):
    serializer_class = serializers.Serializer
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
            data = {
                'username': user.username,
                'key': user.auth_token.key
            }
            return UserTokenSerializer(data).data
            

# TODO: Clean below:
############ To be deleted ########
class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny, )
    token_model = TokenModel

    def get_response_data(self, user):
        if allauth_settings.EMAIL_VERIFICATION == \
                allauth_settings.EmailVerificationMethod.MANDATORY:
            return {}

        if getattr(settings, 'REST_USE_JWT', False):
            data = {
                'user': user,
                'token': self.token
            }
            return JWTSerializer(data).data
        else:
            return TokenSerializer(user.auth_token).data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(self.get_response_data(user), status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(user)
        else:
            create_token(self.token_model, user, serializer)

        complete_signup(self.request._request, user,
                        allauth_settings.EMAIL_VERIFICATION,
                        None)
        return user


class VerifyEmailView(APIView, ConfirmEmailView):

    permission_classes = (AllowAny,)
    allowed_methods = ('POST', 'OPTIONS', 'HEAD')

    def post(self, request, *args, **kwargs):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.kwargs['key'] = serializer.validated_data['key']
        confirmation = self.get_object()
        confirmation.confirm(self.request)
        return Response({'message': _('ok')}, status=status.HTTP_200_OK)
