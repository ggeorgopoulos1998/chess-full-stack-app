import os
import json

import stripe
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import PaymentTransaction, Registration, Tournament


# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_API_KEY")


def _occupied_seats_count(tournament):
    """
    Count registrations that reserve a seat.

    paid = paid online
    free = free tournament registration
    pending = cash payment at tournament / unfinished Stripe payment
    """
    return tournament.registrations.filter(
        payment_status__in=["paid", "free", "pending"]
    ).count()


def _has_existing_registration(tournament, user, email):
    """
    Prevent duplicate registrations for the same tournament.
    Rules:
    - authenticated user cannot register twice
    - same email cannot register twice
    """
    registrations = tournament.registrations.all()

    if user.is_authenticated and registrations.filter(user=user).exists():
        return True

    if email and registrations.filter(email=email).exists():
        return True

    return False


def _mark_registration_paid(session_id, tournament=None):
    """
    Central helper to mark a registration and its payment transaction as paid.
    If tournament is provided, only mark registrations for that tournament.
    """
    registration_qs = Registration.objects.filter(stripe_session_id=session_id)

    if tournament is not None:
        registration_qs = registration_qs.filter(tournament=tournament)

    registration = registration_qs.first()
    if not registration:
        return None

    if registration.payment_status != "paid":
        registration.payment_status = "paid"
        registration.save(update_fields=["payment_status"])

    PaymentTransaction.objects.filter(
        stripe_session_id=session_id,
        registration=registration
    ).update(
        status="paid",
        payment_status="paid"
    )

    return registration


def create_checkout_session(request, slug):
    if request.method != "POST":
        return redirect("tournament_detail", slug=slug)

    tournament = get_object_or_404(Tournament, slug=slug)

    if not tournament.is_open:
        return redirect(f"/tournaments/{slug}/?closed=1")

    # Form data
    full_name = request.POST.get("full_name")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    club = request.POST.get("club", "")
    elo = request.POST.get("elo")
    notes = request.POST.get("notes", "")

    # ✅ NEW: payment method
    payment_method = request.POST.get("payment_method", "stripe")

    if not all([full_name, email, phone]):
        return redirect(f"/tournaments/{slug}/?error=missing_fields")

    if _has_existing_registration(
        tournament=tournament,
        user=request.user,
        email=email,
    ):
        return redirect(f"/tournaments/{slug}/?duplicate=1")

    if _occupied_seats_count(tournament) >= tournament.max_players:
        return redirect(f"/tournaments/{slug}/?full=1")

    elo_value = int(elo) if elo and elo.strip() else None

    # ✅ FREE TOURNAMENT
    if tournament.price_euro == 0:
        Registration.objects.create(
            tournament=tournament,
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            club=club or None,
            elo=elo_value,
            notes=notes or None,
            payment_status="free"
        )
        return redirect(f"/tournaments/{slug}/?success=1")

    # ✅ CASH PAYMENT (NEW FEATURE)
    if payment_method == "cash":
        Registration.objects.create(
            tournament=tournament,
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            club=club or None,
            elo=elo_value,
            notes=notes or None,
            payment_status="pending"
        )
        return redirect(f"/tournaments/{slug}/?success=1&cash=1")

    # ✅ STRIPE FLOW (unchanged)
    registration = Registration.objects.create(
        tournament=tournament,
        user=request.user if request.user.is_authenticated else None,
        full_name=full_name,
        email=email,
        phone=phone,
        club=club or None,
        elo=elo_value,
        notes=notes or None,
        payment_status="pending"
    )

    host = request.get_host()
    scheme = "https" if request.is_secure() else "http"
    base_url = f"{scheme}://{host}"

    success_url = (
        f"{base_url}/tournaments/{slug}/payment/success/"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = (
        f"{base_url}/tournaments/{slug}/payment/cancel/"
        f"?registration_id={registration.id}"
    )

    try:
        amount_cents = int(tournament.price_euro * 100)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"Συμμετοχή: {tournament.title}",
                        "description": f"Τουρνουά σκάκι - {tournament.location}",
                    },
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=email,
            metadata={
                "registration_id": str(registration.id),
                "tournament_id": str(tournament.id),
                "tournament_slug": slug,
            }
        )

        registration.stripe_session_id = checkout_session.id
        registration.save(update_fields=["stripe_session_id"])

        PaymentTransaction.objects.create(
            registration=registration,
            stripe_session_id=checkout_session.id,
            amount=tournament.price_euro,
            currency="EUR",
            status="initiated",
            payment_status="unpaid",
        )

        return redirect(checkout_session.url)

    except stripe.error.StripeError:
        registration.delete()
        return redirect(f"/tournaments/{slug}/?error=payment_error")


def payment_success(request, slug):
    """
    Handle successful payment return from Stripe.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    session_id = request.GET.get("session_id")

    if not session_id:
        return redirect(f"/tournaments/{slug}/")

    # Only accept registrations that belong to this tournament
    registration = Registration.objects.filter(
        stripe_session_id=session_id,
        tournament=tournament
    ).first()

    if not registration:
        return render(request, "tournaments/payment_success.html", {
            "tournament": tournament,
            "error": True,
            "message": "Δεν βρέθηκε η εγγραφή.",
        })

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            registration = _mark_registration_paid(
                session_id=session_id,
                tournament=tournament
            )

            return render(request, "tournaments/payment_success.html", {
                "tournament": tournament,
                "registration": registration,
                "success": True,
            })

        return render(request, "tournaments/payment_success.html", {
            "tournament": tournament,
            "registration": registration,
            "pending": True,
            "session_id": session_id,
        })

    except stripe.error.StripeError:
        return render(request, "tournaments/payment_success.html", {
            "tournament": tournament,
            "error": True,
            "message": "Σφάλμα κατά τον έλεγχο της πληρωμής.",
        })


def payment_cancel(request, slug):
    """
    Handle cancelled payment from Stripe.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    registration_id = request.GET.get("registration_id")

    # Delete only pending registrations for this tournament
    if registration_id:
        Registration.objects.filter(
            id=registration_id,
            tournament=tournament,
            payment_status="pending"
        ).delete()

    return render(request, "tournaments/payment_cancel.html", {
        "tournament": tournament,
    })


def check_payment_status(request, slug):
    """
    AJAX endpoint to check payment status.
    """
    tournament = get_object_or_404(Tournament, slug=slug)
    session_id = request.GET.get("session_id")

    if not session_id:
        return JsonResponse({"error": "Missing session_id"}, status=400)

    # Only allow checks for registrations that belong to this tournament
    registration = Registration.objects.filter(
        stripe_session_id=session_id,
        tournament=tournament
    ).first()

    if not registration:
        return JsonResponse({"error": "Registration not found"}, status=404)

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        # Update database if paid
        if session.payment_status == "paid":
            _mark_registration_paid(
                session_id=session_id,
                tournament=tournament
            )

        return JsonResponse({
            "status": session.status,
            "payment_status": session.payment_status,
        })

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=500)

def resume_checkout_session(request, slug):
    tournament = get_object_or_404(Tournament, slug=slug)

    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/tournaments/{slug}/")

    registration = Registration.objects.filter(
        tournament=tournament,
        user=request.user,
        payment_status="pending"
    ).first()

    if not registration or not registration.stripe_session_id:
        return redirect(f"/tournaments/{slug}/?error=no_pending_payment")

    try:
        session = stripe.checkout.Session.retrieve(registration.stripe_session_id)

        # If Stripe session is still open, redirect user back to it
        if getattr(session, "url", None) and session.status == "open":
            return redirect(session.url)

        # If already paid, sync status and go back
        if session.payment_status == "paid":
            registration.payment_status = "paid"
            registration.save(update_fields=["payment_status"])

            PaymentTransaction.objects.filter(
                stripe_session_id=registration.stripe_session_id
            ).update(status="paid", payment_status="paid")

            return redirect(f"/tournaments/{slug}/?success=1")

        return redirect(f"/tournaments/{slug}/?error=session_expired")

    except stripe.error.StripeError:
        return redirect(f"/tournaments/{slug}/?error=payment_error")


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                webhook_secret
            )
        else:
            # For development without webhook signature verification
            event = json.loads(payload)

    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]

        if session.get("payment_status") == "paid":
            _mark_registration_paid(session_id=session_id)

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        session_id = session["id"]

        PaymentTransaction.objects.filter(
            stripe_session_id=session_id
        ).update(
            status="expired",
            payment_status="expired"
        )

        Registration.objects.filter(
            stripe_session_id=session_id,
            payment_status="pending"
        ).delete()

    return HttpResponse(status=200)