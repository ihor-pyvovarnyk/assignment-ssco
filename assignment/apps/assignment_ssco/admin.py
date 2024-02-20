from django.contrib import admin
from django.db.models import Avg

from assignment.apps.assignment_ssco.models import PointOfInterest


class PointOfInterestAdmin(admin.ModelAdmin):
    model = PointOfInterest
    list_display = ['internal_id', 'name', 'external_id', 'category_name', 'avg_rating']
    search_fields = ['internal_id', 'external_id']
    list_filter = ['category__name']

    @admin.display
    def category_name(self, obj: PointOfInterest) -> str:
        return obj.category.name

    @admin.display
    def avg_rating(self, obj: PointOfInterest) -> float:
        return obj.ratings.aggregate(Avg('rating'))['rating__avg']


admin.site.register(PointOfInterest, PointOfInterestAdmin)
