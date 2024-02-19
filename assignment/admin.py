from django.contrib import admin
from django.db.models import Avg

from assignment.models import PointOfInterest


class PointOfInterestAdmin(admin.ModelAdmin):
    model = PointOfInterest
    list_display = ['internal_id', 'name', 'external_id', 'category', 'avg_rating']
    search_fields = ['internal_id', 'external_id']
    list_filter = ['category']

    @admin.display
    def avg_rating(self, obj: PointOfInterest):
        return obj.ratings.aggregate(Avg('rating'))['rating__avg']


admin.site.register(PointOfInterest, PointOfInterestAdmin)
