from django.contrib.postgres.fields import ArrayField
from django.db import models


class Product(models.Model):
    title = models.CharField(max_length=500, null=True)
    color = models.CharField(max_length=255, null=True)
    memory = models.CharField(max_length=255, null=True)
    manufacturer = models.CharField(max_length=255, null=True)
    price = models.CharField(max_length=255, null=True)
    sale_price = models.CharField(max_length=255, null=True)
    product_code = models.CharField(max_length=255, null=True)
    reviews_count = models.IntegerField(null=True)
    screen_diagonal = models.CharField(max_length=255, null=True)
    screen_resolution = models.CharField(max_length=255, null=True)

    images = ArrayField(models.URLField(max_length=500, null=True), null=True)
    characteristics = models.JSONField(null=True, blank=True)

    search_query = models.CharField(max_length=255, null=True)
    link = models.URLField(max_length=500, null=True)
