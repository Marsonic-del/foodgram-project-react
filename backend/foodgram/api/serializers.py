from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('email', 'username', 'first_name', 'last_name', 'id', 'password', 'is_subscribed')
        model = User
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TokenSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=False, label='Email address', max_length=254, required=True)
    password = serializers.CharField(allow_blank=False, label='password', max_length=150, required=True)


class ChangePasswordSerializer(serializers.ModelSerializer):
    """
    Serializer for password change endpoint.
    """
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    class Meta:
        fields = ('current_password', 'new_password')
        model = User
        extra_kwargs = {'current_password': {'write_only': True},
                        'new_password': {'write_only': True}}

    def update(self, instance, validated_data):
        if not check_password(validated_data['current_password'], instance.password):
            raise ValidationError({'detail': 'current_password is incorrect'})
        instance.set_password(validated_data.get('new_password'))
        instance.save()
        return instance
