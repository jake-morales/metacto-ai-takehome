from django.db import models


class CompanyGoals(models.Model):
    mission = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Company Goals"

    @classmethod
    def get_or_create_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Company Goals"
