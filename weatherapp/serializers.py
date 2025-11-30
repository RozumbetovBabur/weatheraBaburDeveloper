# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2', 'region', 'city']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Parollar uyqas emes."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'region', 'city']

class TokenSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
