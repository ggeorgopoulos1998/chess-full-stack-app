from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime

from .models import TrainingSession
from .forms import TrainingBookingForm


def training_list(request):
    selected_date = request.GET.get("date")

    sessions = TrainingSession.objects.filter(is_open=True).order_by("date")

    if selected_date:
        try:
            parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            sessions = sessions.filter(date__date=parsed_date)
        except ValueError:
            selected_date = None

    return render(request, "trainings/list.html", {
        "sessions": sessions,
        "selected_date": selected_date,
    })


def training_detail(request, id):
    session = get_object_or_404(TrainingSession, id=id)

    if request.method == "POST":
        if not session.is_open:
            return redirect(f"/trainings/{session.id}/?closed=1")

        email = request.POST.get("email")

        existing_booking = session.bookings.filter(email=email).exists()
        if request.user.is_authenticated:
            existing_booking = existing_booking or session.bookings.filter(user=request.user).exists()

        if existing_booking:
            return redirect(f"/trainings/{session.id}/?duplicate=1")

        if session.bookings.count() >= session.max_participants:
            return redirect(f"/trainings/{session.id}/?full=1")

        form = TrainingBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.training_session = session

            if request.user.is_authenticated:
                booking.user = request.user

            booking.save()
            return redirect(f"/trainings/{session.id}/?success=1")
    else:
        form = TrainingBookingForm()

    bookings_count = session.bookings.count()
    is_full = bookings_count >= session.max_participants

    return render(request, "trainings/detail.html", {
        "session": session,
        "bookings_count": bookings_count,
        "is_full": is_full,
        "form": form,
        "success": request.GET.get("success") == "1",
        "full_message": request.GET.get("full") == "1",
        "closed_message": request.GET.get("closed") == "1",
        "duplicate_message": request.GET.get("duplicate") == "1",
    })