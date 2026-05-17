from django.contrib.auth.models import User
from django.db import models


class Tournament(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    image = models.ImageField(
        upload_to="tournaments/",
        blank=True,
        null=True
    )

    category = models.CharField(max_length=100)
    location = models.CharField(max_length=255)

    date = models.DateTimeField()
    start_time = models.CharField(max_length=10)

    price_euro = models.IntegerField(default=0)
    max_players = models.IntegerField()

    system = models.CharField(max_length=100)
    is_open = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title


class Registration(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("free", "Free"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    club = models.CharField(max_length=255, blank=True, null=True)
    elo = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.tournament.title}"


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ("initiated", "Initiated"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("expired", "Expired"),
    ]

    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="payment_transactions"
    )

    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="initiated"
    )
    payment_status = models.CharField(max_length=50, default="unpaid")

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration.full_name} - {self.amount} {self.currency} - {self.status}"


class TournamentPostponementRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="postponement_requests"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tournament_postponement_requests"
    )

    requested_date = models.DateField()
    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    admin_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.registration.full_name} - {self.registration.tournament.title} - {self.requested_date}"