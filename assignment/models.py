from django.db import models


class PointOfInterest(models.Model):
    internal_id = models.AutoField(primary_key=True)
    external_id = models.BigIntegerField()
    name = models.TextField()
    description = models.TextField()
    coordinates = models.ForeignKey(
        'PointOfInterestCoordinates', related_name='point_of_interest', on_delete=models.CASCADE
    )
    category = models.TextField()  # TODO: Make separate table for categories


class PointOfInterestRating(models.Model):
    rating = models.FloatField()
    point_of_interest = models.ForeignKey(
        PointOfInterest, related_name='ratings', on_delete=models.CASCADE
    )


class PointOfInterestCoordinates(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
