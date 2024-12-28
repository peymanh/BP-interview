import datetime
import numpy as np

from celery import shared_task
from .models import Rating, Article


def average_rating(ratings, method):
    if method == "simple_average":
        total_rates = sum(r.rate for r in ratings)
        rate_number = ratings.count()
        return total_rates / rate_number if rate_number > 0 else 0
    elif method == "ageing_weight":
        # Calculate weighted average
        now = datetime.datetime.now().date()
        total_weighted_rates = 0
        total_weights = 0
        for r in ratings:
            age = (now - r.timestamp.date()).seconds  # Calculate age of the rating
            weight = 1 / (1 + age)  # Calculate weight (older ratings have more weight)
            total_weighted_rates += r.rate * weight
            total_weights += weight
        return total_weighted_rates / total_weights if total_weights > 0 else 0
    elif method == "decay":
        decay_factor = 0.9
        ratings = [r.rate for r in ratings]
        weights = np.power(decay_factor, np.arange(len(ratings))[::-1])
        weights /= np.sum(weights)  # Normalize weights to sum to 1

        # Calculate the weighted average
        weighted_average = np.sum(ratings * weights)

        return weighted_average


@shared_task
def update_rating(article_id):
    # Update article's average_rate and rate_number
    article = Article.objects.get(id=article_id)
    ratings = Rating.objects.filter(article=article)
    total_rates = sum(r.rate for r in ratings)
    rate_number = ratings.count()

    # article.average_rate = average_rating(ratings=ratings, method="simple_average")
    # article.average_rate = average_rating(ratings=ratings, method="ageing_weight")
    article.average_rate = average_rating(ratings=ratings, method="decay")
    article.rate_number = rate_number
    article.save()
    return True