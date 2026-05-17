from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm

from tournaments.models import Registration, TournamentPostponementRequest
from trainings.models import TrainingBooking


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("/tournaments/")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/tournaments/")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard_view(request):
    # 🎯 User tournament registrations
    registrations = Registration.objects.filter(user=request.user).select_related("tournament")

    # ⏳ User postponement requests
    postponements = TournamentPostponementRequest.objects.filter(
        user=request.user
    ).select_related("registration__tournament")

    # 🏋️ Training bookings
    training_bookings = TrainingBooking.objects.filter(
        user=request.user
    ).select_related("training_session")

    return render(request, "accounts/dashboard.html", {
        "registrations": registrations,
        "postponements": postponements,
        "training_bookings": training_bookings,
    })