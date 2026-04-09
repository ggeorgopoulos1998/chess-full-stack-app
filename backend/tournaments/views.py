from django.shortcuts import render, get_object_or_404, redirect
from .forms import RegistrationForm, TournamentPostponementRequestForm
from .models import Tournament, Registration, TournamentPostponementRequest


def tournament_list(request):
    tournaments = Tournament.objects.all()
    return render(request, "tournaments/list.html", {
        "tournaments": tournaments
    })


def tournament_calendar(request):
    selected_date = request.GET.get("date")
    tournaments = []

    if selected_date:
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            tournaments = Tournament.objects.filter(date__date=parsed_date).order_by("date")
        except ValueError:
            selected_date = None

    return render(request, "tournaments/calendar.html", {
        "selected_date": selected_date,
        "tournaments": tournaments,
    })


def tournament_detail(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    user_registration = None
    postponement_form = None
    user_postponements = TournamentPostponementRequest.objects.none()
    existing_pending_request = False

    if request.user.is_authenticated:
        user_registration = Registration.objects.filter(
            tournament=tournament,
            user=request.user
        ).first()

        if user_registration:
            user_postponements = TournamentPostponementRequest.objects.filter(
                user=request.user,
                registration=user_registration
            ).order_by("-created_at")

            existing_pending_request = user_postponements.filter(status="pending").exists()

    if request.method == "POST":
        if "register_submit" in request.POST:
            if tournament.registrations.count() >= tournament.max_players:
                return redirect(f"/tournaments/{tournament.slug}/?full=1")

            form = RegistrationForm(request.POST)
            if form.is_valid():
                registration = form.save(commit=False)
                registration.tournament = tournament
                if request.user.is_authenticated:
                    registration.user = request.user
                registration.save()
                return redirect(f"/tournaments/{tournament.slug}/?success=1")
            postponement_form = TournamentPostponementRequestForm()

        elif "postponement_submit" in request.POST:
            if not request.user.is_authenticated or not user_registration:
                return redirect(f"/tournaments/{tournament.slug}/")

            if existing_pending_request:
                return redirect(f"/tournaments/{tournament.slug}/?already_pending=1")

            postponement_form = TournamentPostponementRequestForm(request.POST)
            if postponement_form.is_valid():
                postponement_request = postponement_form.save(commit=False)
                postponement_request.registration = user_registration
                postponement_request.user = request.user
                postponement_request.save()
                return redirect(f"/tournaments/{tournament.slug}/?postponement_success=1")

            form = RegistrationForm()
        else:
            form = RegistrationForm()
            postponement_form = TournamentPostponementRequestForm()
    else:
        form = RegistrationForm()
        postponement_form = TournamentPostponementRequestForm()

    if postponement_form is None:
        postponement_form = TournamentPostponementRequestForm()

    registrations_count = tournament.registrations.count()
    is_full = registrations_count >= tournament.max_players

    return render(request, "tournaments/detail.html", {
        "tournament": tournament,
        "form": form,
        "postponement_form": postponement_form,
        "user_registration": user_registration,
        "user_postponements": user_postponements,
        "existing_pending_request": existing_pending_request,
        "success": request.GET.get("success") == "1",
        "postponement_success": request.GET.get("postponement_success") == "1",
        "already_pending": request.GET.get("already_pending") == "1",
        "full_message": request.GET.get("full") == "1",
        "is_full": is_full,
        "registrations_count": registrations_count,
    })