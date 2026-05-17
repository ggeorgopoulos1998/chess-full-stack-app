from django.urls import path
from . import views
from . import payments

urlpatterns = [
    path("", views.tournament_list, name="tournament_list"),
    path("calendar/", views.tournament_calendar, name="tournament_calendar"),

    # Payment URLs (must be before the slug catch-all)
    path("<slug:slug>/checkout/", payments.create_checkout_session, name="tournament_checkout"),
    path("<slug:slug>/payment/success/", payments.payment_success, name="payment_success"),
    path("<slug:slug>/payment/cancel/", payments.payment_cancel, name="payment_cancel"),
    path("<slug:slug>/payment/status/", payments.check_payment_status, name="payment_status"),
    path("<slug:slug>/payment/resume/", payments.resume_checkout_session, name="resume_checkout"),
    # Tournament detail (last - catches remaining slug patterns)
    path("<slug:slug>/", views.tournament_detail, name="tournament_detail"),

]