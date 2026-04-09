from django.urls import path
from . import views

urlpatterns = [
    path("", views.training_list, name="training_list"),
    path("<int:id>/", views.training_detail, name="training_detail"),
]