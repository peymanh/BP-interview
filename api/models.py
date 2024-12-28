from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=180)
    content = models.CharField(max_length=5000)
    average_rate = models.FloatField(default=0)
    rate_number = models.IntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    rate = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(5), MinValueValidator(0)]
    )
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)




