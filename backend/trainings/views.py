from django.shortcuts import render, get_object_or_404, redirect
from .models import TrainingSession
from .forms import TrainingBookingForm


def training_list(request):
    sessions = TrainingSession.objects.filter(is_open=True).order_by("date")
    return render(request, "trainings/list.html", {
        "sessions": sessions
    })


def training_detail(request, id):
    session = get_object_or_404(TrainingSession, id=id)

    if request.method == "POST":
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
    })