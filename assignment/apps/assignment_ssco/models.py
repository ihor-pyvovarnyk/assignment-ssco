from django.db import models


class PointOfInterest(models.Model):
    internal_id = models.AutoField(primary_key=True)
    external_id = models.BigIntegerField(unique=True)
    name = models.TextField()
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.ForeignKey(
        "PointOfInterestCategory", related_name='point_of_interest', on_delete=models.CASCADE
    )


class PointOfInterestRating(models.Model):
    rating = models.FloatField()
    index = models.SmallIntegerField()
    point_of_interest = models.ForeignKey(
        PointOfInterest, related_name='ratings', on_delete=models.CASCADE
    )

    class Meta:
        indexes = [models.Index(fields=["point_of_interest"])]


class PointOfInterestCategory(models.Model):
    name = models.TextField(unique=True)
