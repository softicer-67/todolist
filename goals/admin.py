from django.contrib import admin

from .models import GoalCategory


@admin.register(GoalCategory)
class GoalCategory(admin.ModelAdmin):
    pass
