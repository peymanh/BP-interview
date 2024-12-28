from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Article, Rating

class UserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = User
        fields = ['id', 'username', 'password', 'email']


class ArticleSerializer(serializers.ModelSerializer):
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'average_rate', 'rate_number', 'user_rating']

    def get_user_rating(self, obj):
        user = self.context['request'].user
        try:
            return obj.rating_set.get(user=user).rate
        except Rating.DoesNotExist:
            return None
        return None

