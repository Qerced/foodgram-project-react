from django.db.models import Sum, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api import serializers
from api.filters import RecipeFilter, IngredientFilter
from api.pagination import PageLimitPagination
from api.permissions import AdminOrReadOnly, AuthorAdminOrReadOnly
from api.util import add_or_del_obj
from recipes import models


class TagViewSet(viewsets.ModelViewSet):
    """Получает список тегов."""
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None
    # На уровне проекта не переопределялся класс пагинации по умолчанию.


class IngredientViewSet(viewsets.ModelViewSet):
    """Получает список ингредиентов."""
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Создаёт и получает список рецептов, также добавляет их в
    корзину и список избранного."""
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.FullRecipeSerializer
    permission_classes = (AuthorAdminOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in (
            'favorite',
            'shopping_cart',
            'download_shopping_cart'
        ):
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    @action(['post', 'delete'], detail=False,
            url_path=r'(?P<recipe_id>\d+)/favorite')
    def favorite(self, request, recipe_id):
        """Добавить или удалить из избранного
        post добавляет, delete убирает из этого списка."""
        error_message = {
            'error_create_obj':
            {'error': 'Рецепт уже находится в списке избранного.'},
            'error_del_obj':
            {'error': 'Рецепт не в списке избранного.'}
        }
        serializer = serializers.RecipeSerializer
        return add_or_del_obj(request, Q(recipe__id=recipe_id),
                              models.Recipe, models.FavoriteRecipe,
                              serializer, error_message, recipe_id)

    @action(['post', 'delete'], detail=False,
            url_path=r'(?P<recipe_id>\d+)/shopping_cart')
    def shopping_cart(self, request, recipe_id):
        error_message = {
            'error_create_obj':
            {'error': 'Рецепт уже находится в корзине.'},
            'error_del_obj':
            {'error': 'Рецепт не находится в корзине.'}
        }
        serializer = serializers.RecipeSerializer
        return add_or_del_obj(request, Q(recipe__id=recipe_id),
                              models.Recipe, models.ShoppingCart,
                              serializer, error_message, recipe_id)

    @action(['get'], detail=False)
    def download_shopping_cart(self, request, *args, **kwargs):
        user = request.user
        if not models.ShoppingCart.objects.filter(user=user).exists():
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)
        file_content = []
        shopping_list = models.Ingredient.objects.filter(
            recipes__user_cart__user=user).values(
            'name',
            'measurement_unit'
        ).annotate(
            amount=Sum('ingredientrecipeamount__amount')
        ).order_by('name')
        for ingredients in shopping_list:
            file_content.append(
                f'{ingredients["name"]}'
                f'({ingredients["measurement_unit"]})—'
                f'{ingredients["amount"]}'
            )
        file_content = '\n'.join(file_content)
        response = HttpResponse(file_content,
                                content_type='text.txt')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response
