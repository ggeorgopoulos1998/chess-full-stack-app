from django.contrib import admin
from .models import Tournament, Registration, TournamentPostponementRequest


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "category", "max_players", "is_open")
    search_fields = ("title", "category", "location")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "tournament", "created_at")
    search_fields = ("full_name", "email", "phone")
    list_filter = ("tournament", "created_at")


@admin.register(TournamentPostponementRequest)
class TournamentPostponementRequestAdmin(admin.ModelAdmin):
    list_display = (
        "registration",
        "user",
        "requested_date",
        "status",
        "created_at",
    )
    list_editable = ("status",)
    search_fields = (
        "registration__full_name",
        "registration__email",
        "registration__tournament__title",
    )
    list_filter = ("status", "requested_date", "created_at")