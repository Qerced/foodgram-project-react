from django.contrib import admin

from recipes import models


class IngredientInline(admin.TabularInline):
    model = models.IngredientRecipeAmount
    fields = ('ingredient', 'amount')


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorite')
    fields = (
        'name', 'author', 'text', 'image', 'cooking_time', 'tags'
    )
    list_filter = ('author', 'tags')
    search_fields = ('author', 'name', 'tags')
    inlines = (IngredientInline,)

    @admin.display(description='Добавлен в избранное')
    def count_favorite(self, obj):
        return obj.favoriterecipe_set.count()


@admin.register(models.FavoriteRecipe)
class FavoriteRecipe(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(models.ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe')
