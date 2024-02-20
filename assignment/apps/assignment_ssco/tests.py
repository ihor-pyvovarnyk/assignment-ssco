from django.core.management import call_command
from django.test import TestCase

from assignment.apps.assignment_ssco.models import PointOfInterest, PointOfInterestCategory, PointOfInterestRating


class AnimalTestCase(TestCase):
    def setUp(self):
        self.fixture_pois_1 = './assignment/apps/assignment_ssco/fixtures/pois_1.json'

    def test_import_file(self):
        with open(self.fixture_pois_1) as f:
            call_command('import_file', file=[f])

        self.assert_(len(PointOfInterest.objects.all()) == 1)
        self.assert_(len(PointOfInterestCategory.objects.all()) == 1)
        self.assert_(len(PointOfInterestRating.objects.all()) == 10)

    def test_import_same_file_twice(self):
        with open(self.fixture_pois_1) as f:
            call_command('import_file', file=[f])
            f.seek(0)
            call_command('import_file', file=[f])

        self.assert_(len(PointOfInterest.objects.all()) == 1)
        self.assert_(len(PointOfInterestCategory.objects.all()) == 1)
        self.assert_(len(PointOfInterestRating.objects.all()) == 10)
