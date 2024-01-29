from django.db.models import Q
from rest_framework import status, generics, views, viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api import serializers
from api.pagination import PageLimitPagination
from api.util import add_or_del_obj
from user.permissions import CreateUserOrAdminOrReadOnly
from user.models import User, Follow
from user.utils import login_user, logout_user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = (CreateUserOrAdminOrReadOnly,)
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in (
            'subscribtions',
            'subscribe',
            'me',
            'set_password'
        ):
            self.permission_classes = (
                permissions.IsAuthenticated,
            )
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return serializers.SubscribeSerializer
        if self.action == 'create':
            return serializers.UserCreateSerializer
        if self.action == 'me':
            return serializers.UserSerializer
        if self.action == 'set_password':
            return serializers.SetPasswordSerializer
        return self.serializer_class

    def get_instance(self):
        return self.request.user

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(['post'], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(
            serializer.data['new_password']
        )
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        pages = self.paginate_queryset(
            User.objects.filter(following__user=request.user)
        )
        serializer = self.get_serializer(pages, many=True)
        return self.get_paginated_response(serializer.data)

    @action(['post', 'delete'], detail=False,
            url_path=r'(?P<author_id>\d+)/subscribe')
    def subscribe(self, request, author_id):
        error_message = {
            'error_create_myself':
            {'error': 'Нельзя подписаться на себя.'},
            'error_create_obj':
            {'error': 'Автор уже находится в списке подписок.'},
            'error_del_obj':
            {'error': 'Автор не находится в списке подписок.'}
        }
        if request.user.id == int(author_id):
            return Response(
                error_message['error_create_myself'],
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = serializers.SubscribeSerializer
        return add_or_del_obj(request, Q(author__id=author_id),
                              User, Follow, serializer,
                              error_message, author_id)


class TokenCreateView(generics.GenericAPIView):
    serializer_class = serializers.TokenCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._action(serializer)

    def _action(self, serialzier):
        token = login_user(self.request, serialzier.user)
        token_serializer_class = serializers.TokenSerializer
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_200_OK
        )


class TokenDestroyView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
