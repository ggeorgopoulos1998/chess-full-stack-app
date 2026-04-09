from django.contrib import admin
from .models import Coach, TrainingSession, TrainingBooking


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "specialty", "is_active")
    search_fields = ("first_name", "last_name", "specialty")
    prepopulated_fields = {"slug": ("first_name", "last_name")}


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "coach",
        "date",
        "session_type",
        "max_participants",
        "price_euro",
        "is_open",
    )
    search_fields = ("title", "coach__first_name", "coach__last_name")
    list_filter = ("session_type", "is_open", "coach")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TrainingBooking)
class TrainingBookingAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "training_session", "created_at")
    search_fields = ("full_name", "email", "phone", "training_session__title")
    list_filter = ("training_session", "created_at")