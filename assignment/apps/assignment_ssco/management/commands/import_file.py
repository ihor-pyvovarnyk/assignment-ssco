import argparse
import csv
import json
import os.path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Iterator, TextIO, Type
from xml.etree import ElementTree

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Model

from assignment.apps.assignment_ssco.models import PointOfInterest, PointOfInterestRating, PointOfInterestCategory


class Command(BaseCommand):
    BULK_SIZE = 1000

    @property
    def readers_by_extension(self) -> dict[str, Type["AbstractReader"]]:
        return {
            '.json': JsonReader,
            '.csv': CsvReader,
            '.xml': XmlReader,
        }

    def add_arguments(self, parser):
        parser.add_argument('--file', '-f', type=argparse.FileType('r'), nargs='+')

    def handle(self, *args, **options):
        for file in options['file']:
            self.stdout.write(f'Processing file: {file.name}')
            reader = self._create_reader(file)
            with transaction.atomic():
                models_iter = self._create_models(reader)
                for pois, categories, ratings in self._chunkify_models(models_iter, self.BULK_SIZE):
                    # NOTE: This implementation upserts the data so import of the same
                    # file twice would not create duplicate data. In the context of this
                    # assignment there're two issues that I decided to ignore to not
                    # spend too much time on the assignment:
                    # 1. Unnecessary updates for potentially unchanged data
                    #    (for categories and ratings tables)
                    # 2. Ratings for each PoI are deleted and new values inserted which
                    #    isn't particularly efficient but allows to properly synchronize
                    #    the ratings

                    PointOfInterestCategory.objects.bulk_create(
                        categories,
                        update_conflicts=True,
                        unique_fields=['name'],
                        update_fields=['name'],
                    )

                    PointOfInterest.objects.bulk_create(
                        pois,
                        update_conflicts=True,
                        unique_fields=['external_id'],
                        update_fields=[
                            f.name for f in PointOfInterest._meta.fields
                            if f.name != 'external_id' and not f.primary_key
                        ],
                    )

                    PointOfInterestRating.objects.filter(
                        point_of_interest_id__in=[p.internal_id for p in pois]
                    ).delete()
                    PointOfInterestRating.objects.bulk_create(ratings)

        self.stdout.write('Done')

    def _create_reader(self, file: TextIO) -> "AbstractReader":
        extension = os.path.splitext(file.name)[1]
        reader_factory = self.readers_by_extension[extension]
        return reader_factory(file)

    @staticmethod
    def _create_models(reader: "AbstractReader") -> Generator[tuple[Model, Model, list[Model]], None, None]:
        for record in reader:
            category = PointOfInterestCategory(
                name=record.category,
            )
            poi = PointOfInterest(
                external_id=record.external_id,
                name=record.name,
                description=record.description,
                latitude=record.coordinates_latitude,
                longitude=record.coordinates_longitude,
                category=category,
            )
            ratings = [
                PointOfInterestRating(
                    rating=rating,
                    index=idx,
                    point_of_interest=poi,
                )
                for idx, rating in enumerate(record.ratings)
            ]
            yield poi, category, ratings

    @staticmethod
    def _chunkify_models(
        models_iter: Iterator[tuple[Model, Model, list[Model]]], size: int
    ) -> Generator[tuple[list[Model], list[Model], list[Model]], None, None]:
        result = None
        for models in models_iter:
            if result is None:
                result = tuple([] for _ in range(len(models)))
            for model, result_models in zip(models, result):
                if isinstance(model, list):
                    result_models.extend(model)
                else:
                    result_models.append(model)
            if len(result[0]) > size:
                yield result
                result = None
        if result and any(result):
            yield result


@dataclass
class PointOfInterestImportModel:
    external_id: int
    name: str
    coordinates_latitude: float
    coordinates_longitude: float
    category: str
    ratings: list[float]
    description: str = ''


class AbstractReader(ABC):
    def __init__(self, file: TextIO):
        self.file = file

    @abstractmethod
    def __iter__(self) -> Generator[PointOfInterestImportModel, None, None]:
        yield


class JsonReader(AbstractReader):
    def __iter__(self) -> Generator[PointOfInterestImportModel, None, None]:
        data = json.load(self.file)
        for row in data:
            yield PointOfInterestImportModel(
                external_id=row['id'],
                name=row['name'],
                description=row.get('description', ''),
                coordinates_latitude=float(row['coordinates']['latitude']),
                coordinates_longitude=float(row['coordinates']['longitude']),
                category=row['category'],
                ratings=self._parse_records(row['ratings']),
            )

    @staticmethod
    def _parse_records(ratings: list[int]) -> list[float]:
        return [float(r) for r in ratings]


class CsvReader(AbstractReader):
    def __iter__(self) -> Generator[PointOfInterestImportModel, None, None]:
        reader = csv.DictReader(self.file, delimiter=',')
        for row in reader:
            yield PointOfInterestImportModel(
                external_id=row['poi_id'],
                name=row['poi_name'],
                description=row.get('poi_description', ''),
                coordinates_latitude=float(row['poi_latitude']),
                coordinates_longitude=float(row['poi_longitude']),
                category=row['poi_category'],
                ratings=self._parse_records(row['poi_ratings']),
            )

    @staticmethod
    def _parse_records(ratings: str) -> list[float]:
        return [float(r) for r in ratings[1:-1].split(',')]


class XmlReader(AbstractReader):
    def __iter__(self) -> Generator['PointOfInterestImportModel', None, None]:
        tree = ElementTree.parse(self.file)
        records = tree.getroot()
        for data_record in records:
            row = {field.tag: field.text for field in data_record}
            yield PointOfInterestImportModel(
                external_id=row['pid'],
                name=row['pname'],
                description=row.get('pdescription', ''),
                coordinates_latitude=float(row['platitude']),
                coordinates_longitude=float(row['plongitude']),
                category=row['pcategory'],
                ratings=self._parse_records(row['pratings']),
            )

    @staticmethod
    def _parse_records(ratings: str) -> list[float]:
        return [float(r) for r in ratings.split(',')]
