from django.urls import path
from . import views

urlpatterns = [
    path("", views.tournament_list, name="tournament_list"),
    path("calendar/", views.tournament_calendar, name="tournament_calendar"),
    path("<slug:slug>/", views.tournament_detail, name="tournament_detail"),
]