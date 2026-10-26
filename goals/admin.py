from django.contrib import admin
from .models import CompanyGoals


@admin.register(CompanyGoals)
class CompanyGoalsAdmin(admin.ModelAdmin):
    list_display = ["__str__", "updated_at"]
