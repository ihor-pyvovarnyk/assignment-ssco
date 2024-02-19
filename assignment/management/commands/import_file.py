import argparse
import csv
import json
import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator
from xml.etree import ElementTree

from django.core.management.base import BaseCommand
from django.db import transaction

from assignment.models import PointOfInterest, PointOfInterestRating, PointOfInterestCoordinates


class Command(BaseCommand):
    BULK_SIZE = 1000

    @property
    def readers_by_extension(self):
        return {
            '.json': JsonReader,
            '.csv': CsvReader,
            '.xml': XmlReader,
        }

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', type=argparse.FileType('r'), nargs='+')

    def handle(self, *args, **options):
        for file in options['file']:
            print(f"Processing file: {file.name}")
            reader_factory = self.readers_by_extension[os.path.splitext(file.name)[1]]
            reader = reader_factory(file)
            with transaction.atomic():
                all_coordinates = []
                all_pois = []
                all_ratings = []
                for record in reader:
                    coordinates = PointOfInterestCoordinates(
                        latitude=record.coordinates_latitude,
                        longitude=record.coordinates_longitude,
                    )
                    poi = PointOfInterest(
                        external_id=record.external_id,
                        name=record.name,
                        description=record.description,
                        coordinates=coordinates,
                        category=record.category,
                    )
                    ratings = [
                        PointOfInterestRating(
                            rating=rating,
                            point_of_interest=poi,
                        )
                        for rating in record.ratings
                    ]
                    all_coordinates.append(coordinates)
                    all_pois.append(poi)
                    all_ratings.extend(ratings)
                    if len(all_pois) > self.BULK_SIZE:
                        # TODO: Make this less ugly
                        PointOfInterestCoordinates.objects.bulk_create(all_coordinates)
                        PointOfInterest.objects.bulk_create(all_pois)
                        PointOfInterestRating.objects.bulk_create(all_ratings)
                        all_coordinates = []
                        all_pois = []
                        all_ratings = []

                if all_pois:
                    PointOfInterestCoordinates.objects.bulk_create(all_coordinates)
                    PointOfInterest.objects.bulk_create(all_pois)
                    PointOfInterestRating.objects.bulk_create(all_ratings)


class AbstractReader(ABC):
    def __init__(self, file):
        self.file = file

    @abstractmethod
    def __iter__(self) -> Generator['PointOfInterestImportModel', None, None]:
        yield


class JsonReader(AbstractReader):
    def __iter__(self) -> Generator['PointOfInterestImportModel', None, None]:
        data = json.load(self.file)
        for record in data:
            yield PointOfInterestImportModel(
                external_id=record['id'],
                name=record['name'],
                description=record.get('description', ''),
                coordinates_latitude=float(record['coordinates']['latitude']),
                coordinates_longitude=float(record['coordinates']['longitude']),
                category=record['category'],
                ratings=record['ratings'],
            )


class CsvReader(AbstractReader):
    def __iter__(self) -> Generator['PointOfInterestImportModel', None, None]:
        reader = csv.DictReader(self.file, delimiter=',')
        for row in reader:
            yield PointOfInterestImportModel(
                external_id=row['poi_id'],
                name=row['poi_name'],
                description=row.get('description', ''),
                coordinates_latitude=float(row['poi_latitude']),
                coordinates_longitude=float(row['poi_longitude']),
                category=row['poi_category'],
                ratings=[float(r) for r in row['poi_ratings'][1:-1].split(',')]
            )


class XmlReader(AbstractReader):
    def __iter__(self) -> Generator['PointOfInterestImportModel', None, None]:
        tree = ElementTree.parse(self.file)
        root = tree.getroot()
        for record in root:
            row = {
                field.tag: field.text
                for field in record
            }
            yield PointOfInterestImportModel(
                external_id=row['pid'],
                name=row['pname'],
                description=row.get('pdescription', ''),
                coordinates_latitude=float(row['platitude']),
                coordinates_longitude=float(row['plongitude']),
                category=row['pcategory'],
                ratings=[float(r) for r in row['pratings'].split(',')]
            )


@dataclass
class PointOfInterestImportModel:
    external_id: int
    name: str
    coordinates_latitude: float
    coordinates_longitude: float
    category: str
    ratings: list[float]
    description: str = ''
