from django.contrib import admin
from django.utils.html import format_html

from .models import Tournament, Registration, TournamentPostponementRequest


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "date",
        "category",
        "max_players",
        "is_open",
        "image_preview",
    )

    search_fields = ("title", "category", "location")
    list_filter = ("category", "is_open", "date")

    prepopulated_fields = {"slug": ("title",)}

    fields = (
        "title",
        "slug",
        "description",
        "image",  # 👈 upload field in admin
        "category",
        "location",
        "date",
        "start_time",
        "price_euro",
        "max_players",
        "system",
        "is_open",
    )

    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:6px;" />',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "phone",
        "tournament",
        "payment_status",
        "created_at",
    )

    search_fields = ("full_name", "email", "phone")
    list_filter = ("tournament", "payment_status", "created_at")


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