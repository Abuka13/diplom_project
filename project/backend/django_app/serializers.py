from django.contrib.auth.models import User
from rest_framework import serializers
from django_app import models


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Product
        fields = '__all__'

    def validate_article(self, value):
        if any(char.isdigit() for char in value):
            raise serializers.ValidationError("Артикул содержит цифру.")
        return value