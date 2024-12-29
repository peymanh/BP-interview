## Introduction

This is sample DRF project, done as the code challenge of Bitpin interview and hiring process.

## Technologies Used
| Name                  | Version |
|-----------------------|---------|
| Python                | 3.11    |
| Django                | 4.2.17  |
| Django Rest Framework | 3.15.2  |
| Celery                | 5.4.0   |
| Redis                 | 6.2.0   |
| Docker                | 23.0.5  |


## Build and run the project With Docker

1. Clone the project:
```bash
git clone https://github.com/peymanh/BP-interview.git
```

2. change directory to the project folder
```bash
cd bp
```
3. Make sure you have installed Docker CLI.
4. Simply run the project with docker compose:
```bash
docker compose up --build
```

Now, the APIs are available on: **localhost:8000**

## APIs Descriptions

| route           | Description                                                          | Method |
|-----------------|----------------------------------------------------------------------|--------|
| /register       | Register new user                                                    | POST   |
| /login          | login the user with username and password                            | POST   |
| /article/create | Creates new article with the specified title and content. AUTHORIZATION needed | POST   |
| /article/rate   | Rated the specified article. AUTHORIZATION needed                    | POST   |
| /articls        | Returns list of article                                              | GET    |


## Implementation Description
__________________
### User model and Authorization

> /register Method: POST

> /login Method: POST

In this project, we have used the default ``User`` model from ``django.contrib.auth.models``.
Users are registered with this sample data:

```json
{
    "username": "peyman",
    "password": "123123",
    "email": "hassanabadi.peyman@gmail.com" // not needed in login api
}
```
and in the response an auth-token is returned that should be used in authorization needed services.

```json
{
    "token": "62cc1a7e77573c08b27d49e610900839b7e714ca",
    "user": {
        "id": 1,
        "username": "peyman",
        "password": "123123",
        "email": "hassanabadi.peyman@gmail.com"
    }
}
```

## Create Article

We have defined an article model like this:
```python
class Article(models.Model):
    title = models.CharField(max_length=180)
    content = models.CharField(max_length=5000)
    average_rate = models.FloatField(default=0)
    rate_number = models.IntegerField(default=0)
    author = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
```

As you see, the article model contains ``average_rate`` and ``rate_number`` with default values of 0.
When you call the /article/create service, a row is added to the DB with thses column equal to 0. Moreover, the author and the time related fieilds are defined in this model too.

## Rating an article

This is the most important service of the project. To rate an article, we have defined a ``Rating`` model like this:

```python
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    rate = models.IntegerField(
        default=3,
        validators=[MaxValueValidator(5), MinValueValidator(0)]
    )
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
```

As you see in this model, 2 foreign keys are defined which point to the ``Article`` and ``User`` model.
Both of these columns are indexed with ``db_index=True``, because most of our searches on this model are based on these columns.
We have a ``rate`` column in the range of ``[0,5]`` with the specified validators. Moreover we have defined time related fields which are used to calculate the age of rating that is used in calculating the ``average_rate``.

Whenever a user rates and articles, we search through the model to find whether they have rated before. If true, we update the rate and if not, we insert a new row.

## Calculating the average rate
As this rating service is a high-traffic service, the calculation of the average cannot be performed synchronously.
So, a asynchronous task is dispatched to calculate the article's average_rate.

```python
from .tasks import update_rating

update_rating.delay(article_id=article.id) 
```
This way, the Rating model which contains millions of row will is accessed in another thread besides the main thread 
and speeds up the /article/rate API.

When the calulcation is completed, the ``average_rate`` and ``rate_number`` is updated on the article model.
This fields act like a cache for the GET service since there is no need to re-calculate them whenever the /articles service is called.

## Average Methods

In this project we have implemented 3 was to calculate the average.

1. Simple Average

If the service is not loaded too much, we can use this method.
This method simply calculated the average.

```python
total_rates = sum(r.rate for r in ratings)
rate_number = ratings.count()
return total_rates / rate_number if rate_number > 0 else 0
```

2. Ageing Average

As it is supposed in the project description, 
sometimes the rating API is called by thousands of the emotional voters,
we should design a way to decrease the effect of recent voters.

A good way is to weight the rates based on their age. The age of each rate is calculated this way:

```python
age = (now - r.timestamp.date()).seconds  # Calculate age of the rating
weight = 1 / (1 + age)  # Calculate weight (older ratings have more weight)
```
So the older the rate, the more effect on the average!:

```python
for r in ratings:
    age = (now - r.timestamp.date()).seconds  # Calculate age of the rating
    weight = 1 / (1 + age)  # Calculate weight (older ratings have more weight)
    total_weighted_rates += r.rate * weight
    total_weights += weight
return total_weighted_rates / total_weights if total_weights > 0 else 0
```

3. Decaying Average

There is another subsequent way to give more attention to decrease the effect of the recent rates.
The solution is to decay the weight of  the most recent votes:

```python
import numpy as np

decay_factor = 0.9
ratings = [r.rate for r in ratings]
weights = np.power(decay_factor, np.arange(len(ratings))[::-1])
weights /= np.sum(weights)  # Normalize weights to sum to 1

# Calculate the weighted average
weighted_average = np.sum(ratings * weights)

return weighted_average
```

>Note: The downside of this method is that the ``ratings = [r.rate for r in ratings]`` may get too big. 
> But we should have in mind that the rates are a single digit number, equal to 8 bytes,
> so even if we suppose that an article's rate number reaches 1M, we will have 8Mb.
> Considering this calculation for ``weights`` and ``weighted_average`` lists too, this block of code will consume 24Mb.

## Article List

Getting the list of articles is no pain if we already have calculated the average and rate number.
As we explained before, there are asynchronous workers busy calculating those numbers,
so if we read the articles tables, we can be sure that we can be 99.999% sure that the exact average and rate number related to the articles.

>Note: Pay attention that there is no overhead for calculating the average and rate number, as they are already calculated.
> so no database join or search is needed and speed is like a bolt!

There just one challenge: <i>User rate if they have rated an article</i>.
We implement this using the lovely serializers. In the ``ArticleSerializer`` we add this code:

```python
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
```

That ``get_user_rating`` function adds the user rating with a simple join on rating table.

## Stay in touch

- Author - Peyman Hassanabadi


