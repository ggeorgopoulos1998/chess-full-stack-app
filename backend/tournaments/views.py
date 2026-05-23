from django.shortcuts import render, get_object_or_404, redirect

from .forms import RegistrationForm, TournamentPostponementRequestForm
from .models import Tournament, Registration, TournamentPostponementRequest


# 🔹 LIST + DATE FILTER
def tournament_list(request):
    selected_date = request.GET.get("date")

    tournaments = Tournament.objects.all().order_by("date")

    if selected_date:
        from datetime import datetime

        try:
            parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
            tournaments = tournaments.filter(date__date=parsed_date)
        except ValueError:
            selected_date = None

    return render(request, "tournaments/list.html", {
        "tournaments": tournaments,
        "selected_date": selected_date,
    })


# 🔹 DETAIL VIEW (UNCHANGED LOGIC)
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

        # ✅ REGISTER
        if "register_submit" in request.POST:
            if not tournament.is_open:
                return redirect(f"/tournaments/{tournament.slug}/?closed=1")

            existing_registration = False
            email = request.POST.get("email")
            full_name = request.POST.get("full_name")

            if email and full_name and tournament.registrations.filter(
                email=email,
                full_name=full_name
            ).exists():
                existing_registration = True

            if request.user.is_authenticated and tournament.registrations.filter(
                user=request.user
            ).exists():
                existing_registration = True

            if existing_registration:
                return redirect(f"/tournaments/{tournament.slug}/?duplicate=1")

            occupied_count = tournament.registrations.filter(
                payment_status__in=["paid", "free"]
            ).count()

            if occupied_count >= tournament.max_players:
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

        # ✅ POSTPONEMENT
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

    registrations_count = tournament.registrations.filter(
        payment_status__in=["paid", "free", "pending"]
    ).count()

    is_full = registrations_count >= tournament.max_players

    has_user_registration = user_registration is not None
    user_registration_status = user_registration.payment_status if user_registration else None

    show_registration_form = (
        tournament.is_open and
        not is_full and
        not has_user_registration
    )

    return render(request, "tournaments/detail.html", {
        "tournament": tournament,
        "form": form,
        "postponement_form": postponement_form,
        "user_registration": user_registration,
        "user_postponements": user_postponements,
        "existing_pending_request": existing_pending_request,
        "has_user_registration": has_user_registration,
        "user_registration_status": user_registration_status,
        "show_registration_form": show_registration_form,
        "success": request.GET.get("success") == "1",
        "postponement_success": request.GET.get("postponement_success") == "1",
        "already_pending": request.GET.get("already_pending") == "1",
        "full_message": request.GET.get("full") == "1",
        "duplicate_message": request.GET.get("duplicate") == "1",
        "closed_message": request.GET.get("closed") == "1",
        "error_message": request.GET.get("error"),
        "is_full": is_full,
        "registrations_count": registrations_count,
    })