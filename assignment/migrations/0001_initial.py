# Generated by Django 5.0.2 on 2024-02-19 17:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PointOfInterestCoordinates',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='PointOfInterest',
            fields=[
                ('internal_id', models.AutoField(primary_key=True, serialize=False)),
                ('external_id', models.BigIntegerField()),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('category', models.TextField()),
                ('coordinates', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='point_of_interest', to='assignment.pointofinterestcoordinates')),
            ],
        ),
        migrations.CreateModel(
            name='PointOfInterestRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.FloatField()),
                ('point_of_interest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='assignment.pointofinterest')),
            ],
        ),
    ]
