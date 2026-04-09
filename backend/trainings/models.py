from django.contrib.auth.models import User
from django.db import models


class Coach(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    short_bio = models.CharField(max_length=255)
    full_bio = models.TextField(blank=True, null=True)

    specialty = models.CharField(max_length=150, blank=True, null=True)
    photo = models.ImageField(upload_to="coaches/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TrainingSession(models.Model):
    SESSION_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("group", "Group"),
    ]

    coach = models.ForeignKey(
        Coach,
        on_delete=models.CASCADE,
        related_name="training_sessions"
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    date = models.DateTimeField()
    start_time = models.CharField(max_length=10)
    duration_minutes = models.PositiveIntegerField(default=60)

    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default="individual"
    )

    max_participants = models.PositiveIntegerField(default=1)
    price_euro = models.PositiveIntegerField(default=0)

    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.title} - {self.coach}"


class TrainingBooking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_bookings"
    )

    training_session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.training_session.title}"