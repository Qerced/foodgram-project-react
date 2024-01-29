from django.urls import re_path, path, include
from rest_framework.routers import DefaultRouter

from api import views
from user.views import UserViewSet, TokenCreateView, TokenDestroyView


app_name = 'api'
router = DefaultRouter()

router.register('tags', views.TagViewSet, basename='tag')
router.register('ingredients', views.IngredientViewSet, basename='ingredient')
router.register('recipes', views.RecipeViewSet, basename='recipe')
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include([
        re_path(r"^token/login/?$",
                TokenCreateView.as_view(), name="login"),
        re_path(r"^token/logout/?$",
                TokenDestroyView.as_view(), name="logout")
    ]))
]
