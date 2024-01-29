from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError
from django.db.models import F
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from recipes.models import (Ingredient, Recipe, Tag,
                            IngredientRecipeAmount)
from user.models import User


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Cериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.Serializer):
    """Вспомогательный сериализатор игредиентов для валидации и
    создания связи с количеством."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), required=True)
    amount = serializers.IntegerField(min_value=1, required=True)


class TagTagSerializer(serializers.Serializer):
    """Вспомогательный сериализатор тегов для валидации и
    создания связи с рецептом."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор вывода рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор вывода пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()


class FullRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""
    image = Base64ImageField(allow_null=False)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorite_recipes.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.cart_recipes.filter(recipe=obj).exists()

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('ingredientrecipeamount__amount')
        )

    def validate(self, attrs):
        tags = self.initial_data.get('tags')
        tag_serializer = TagTagSerializer(data={'tags': tags})
        tag_serializer.is_valid(raise_exception=True)
        attrs.update(tag_serializer.validated_data)
        ingredients = self.initial_data.get('ingredients')
        lst = []
        for ingredient in ingredients:
            ingredient_serializer = IngredientRecipeSerializer(data=ingredient)
            ingredient_serializer.is_valid(raise_exception=True)
            lst.append(ingredient_serializer.validated_data)
        attrs.update({'ingredients': lst})
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            IngredientRecipeAmount(
                amount=ingredient.get('amount'),
                recipe=recipe,
                ingredient=ingredient.get('id')
            ).save()
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        for ingredient in ingredients:
            IngredientRecipeAmount.objects.get_or_create(
                amount=ingredient.get('amount'),
                recipe=instance,
                ingredient=ingredient.get('id')
            )
        return super().update(instance, validated_data)


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор вывода авторов рецепта на которых подписан
    пользователь."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'recipes',
                  'recipes_count')
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        limit = self.context.get('request').query_params.get('recipes_limit')
        if limit and limit.isdecimal():
            return RecipeSerializer(
                obj.recipes.all()[:int(limit)],
                many=True,
                context=self.context
            ).data
        return RecipeSerializer(obj.recipes.all(),
                                many=True,
                                context=self.context).data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return obj.following.filter(user=user).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей."""
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
        read_only_fields = ('id',)

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get('password')

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {'password': serializer_error['non_field_errors']}
            )

        return attrs

    def create(self, validated_data):
        try:
            return User.objects.create_user(**validated_data)
        except IntegrityError:
            self.fail('cannot_create_user')


class SetPasswordSerializer(serializers.Serializer):
    """Cериализатор для изменения пароля пользователей."""
    new_password = serializers.CharField(
        style={'input_type': 'password'})
    current_password = serializers.CharField(
        style={'input_type': 'password'})

    default_error_messages = {
        'invalid_password': 'Invalid password.'
    }

    def validate(self, attrs):
        user = self.context['request'].user
        try:
            validate_password(attrs['new_password'], user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.message)})
        return super().validate(attrs)

    def validate_current_password(self, value):
        is_password_valid = (
            self.context['request'].user.check_password(value)
        )
        if not is_password_valid:
            self.fail('invalid_password')
        return value


class TokenCreateSerializer(serializers.Serializer):
    """Cериализатор для входа пользователей."""
    password = serializers.CharField(
        required=False, style={'input_type': 'password'})
    email = serializers.EmailField(required=False)

    default_error_messages = {
        'invalid_credentials': 'Неверный пароль.',
        'access error': 'Ошибка доступа.'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        password = attrs.get('password')
        email = attrs.get('email')
        self.user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )
        if not self.user:
            self.user = User.objects.filter(email=email).first()
            if self.user and not self.user.check_password(password):
                self.fail('invalid_credentials')
            if not self.user and not self.user.is_active:
                self.fail('access error')
        return attrs


class TokenSerializer(serializers.ModelSerializer):
    """Сериализатор вывода токена."""
    auth_token = serializers.CharField(source='key')

    class Meta:
        model = Token
        fields = ('auth_token',)
