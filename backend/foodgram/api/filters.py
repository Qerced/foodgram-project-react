from django_filters import rest_framework as filters

from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(
        field_name='author__pk',
        lookup_expr='exact'
    )
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='exact'
    )
    is_favorited = filters.NumberFilter(
        field_name='favoriterecipe',
        method='filter_favorite'
    )
    is_in_shopping_cart = filters.NumberFilter(
        field_name='user_cart',
        method='filter_cart'
    )

    def filter_favorite(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(favoriterecipe__user=user)
        return queryset

    def filter_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return queryset.filter(user_cart__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = 'author', 'tags'


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = 'name',
