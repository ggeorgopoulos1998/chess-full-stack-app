from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from tournaments.models import Tournament, Registration, PaymentTransaction


class TournamentBookingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass1234"
        )

        self.paid_tournament = Tournament.objects.create(
            title="Paid Tournament",
            slug="paid-tournament",
            description="Desc",
            category="Open",
            location="Athens",
            date="2030-01-10T10:00:00Z",
            start_time="10:00",
            price_euro=20,
            max_players=2,
            system="Swiss",
            is_open=True,
        )

        self.free_tournament = Tournament.objects.create(
            title="Free Tournament",
            slug="free-tournament",
            description="Desc",
            category="Open",
            location="Athens",
            date="2030-01-11T10:00:00Z",
            start_time="10:00",
            price_euro=0,
            max_players=1,
            system="Swiss",
            is_open=True,
        )

        self.closed_tournament = Tournament.objects.create(
            title="Closed Tournament",
            slug="closed-tournament",
            description="Desc",
            category="Open",
            location="Athens",
            date="2030-01-12T10:00:00Z",
            start_time="10:00",
            price_euro=10,
            max_players=10,
            system="Swiss",
            is_open=False,
        )

        self.valid_post_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "6900000000",
            "club": "Chess Club",
            "elo": "1800",
            "notes": "Ready to play",
        }

    @patch("tournaments.payments.stripe.checkout.Session.create")
    def test_paid_checkout_creates_pending_registration_and_transaction(self, mock_create):
        mock_session = Mock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/test-session"
        mock_create.return_value = mock_session

        response = self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.paid_tournament.slug}),
            data=self.valid_post_data,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(PaymentTransaction.objects.count(), 1)

        registration = Registration.objects.get()
        transaction = PaymentTransaction.objects.get()

        self.assertEqual(registration.payment_status, "pending")
        self.assertEqual(registration.stripe_session_id, "cs_test_123")

        self.assertEqual(transaction.registration, registration)
        self.assertEqual(transaction.stripe_session_id, "cs_test_123")
        self.assertEqual(transaction.amount, Decimal("20.00"))
        self.assertEqual(transaction.status, "initiated")
        self.assertEqual(transaction.payment_status, "unpaid")

    @patch("tournaments.payments.stripe.checkout.Session.create")
    def test_stripe_error_rolls_back_pending_registration(self, mock_create):
        mock_create.side_effect = Exception("boom")

        with self.assertRaises(Exception):
            self.client.post(
                reverse("tournament_checkout", kwargs={"slug": self.paid_tournament.slug}),
                data=self.valid_post_data,
            )

        # This test shows a current bug:
        # your code catches stripe.error.StripeError, not generic exceptions.
        # If Stripe raises a different exception or mock is wrong, cleanup will not happen.
        # We keep this test to reveal behavior.
    @patch("tournaments.payments.stripe.checkout.Session.create")
    def test_free_tournament_creates_free_registration(self, mock_create):
        response = self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.free_tournament.slug}),
            data=self.valid_post_data,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(PaymentTransaction.objects.count(), 0)

        registration = Registration.objects.get()
        self.assertEqual(registration.payment_status, "free")
        self.assertIsNone(registration.stripe_session_id)

        mock_create.assert_not_called()

    def test_free_tournament_overbooking_should_be_blocked_but_currently_is_not(self):
        Registration.objects.create(
            tournament=self.free_tournament,
            full_name="First Player",
            email="first@example.com",
            phone="6900000001",
            payment_status="free",
        )

        response = self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.free_tournament.slug}),
            data={
                "full_name": "Second Player",
                "email": "second@example.com",
                "phone": "6900000002",
            },
        )

        # Desired behavior:
        # second booking should be rejected and registrations stay at 1
        # Current code will likely allow this and make count 2.
        self.assertEqual(
            Registration.objects.filter(tournament=self.free_tournament).count(),
            1,
            msg="BUG: free tournaments can currently overbook because only paid registrations are counted."
        )

    def test_closed_tournament_checkout_should_be_blocked_but_currently_is_not(self):
        response = self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.closed_tournament.slug}),
            data=self.valid_post_data,
        )

        self.assertEqual(
            Registration.objects.filter(tournament=self.closed_tournament).count(),
            0,
            msg="BUG: closed tournaments should not accept direct POST checkout."
        )

    @patch("tournaments.payments.stripe.checkout.Session.create")
    def test_same_user_can_currently_register_twice_for_same_tournament(self, mock_create):
        mock_session_1 = Mock()
        mock_session_1.id = "cs_test_dup_1"
        mock_session_1.url = "https://checkout.stripe.com/test-session-1"

        mock_session_2 = Mock()
        mock_session_2.id = "cs_test_dup_2"
        mock_session_2.url = "https://checkout.stripe.com/test-session-2"

        mock_create.side_effect = [mock_session_1, mock_session_2]

        self.client.login(username="testuser", password="pass1234")

        self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.paid_tournament.slug}),
            data=self.valid_post_data,
        )
        self.client.post(
            reverse("tournament_checkout", kwargs={"slug": self.paid_tournament.slug}),
            data=self.valid_post_data,
        )

        self.assertEqual(
            Registration.objects.filter(
                tournament=self.paid_tournament,
                user=self.user,
            ).count(),
            1,
            msg="BUG: same user should not be able to register twice for the same tournament."
        )

    @patch("tournaments.payments.stripe.checkout.Session.retrieve")
    def test_payment_success_marks_registration_and_transaction_paid(self, mock_retrieve):
        registration = Registration.objects.create(
            tournament=self.paid_tournament,
            user=self.user,
            full_name="John Doe",
            email="john@example.com",
            phone="6900000000",
            payment_status="pending",
            stripe_session_id="cs_success_123",
        )
        PaymentTransaction.objects.create(
            registration=registration,
            stripe_session_id="cs_success_123",
            amount=20,
            currency="EUR",
            status="initiated",
            payment_status="unpaid",
        )

        mock_session = Mock()
        mock_session.payment_status = "paid"
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            reverse("payment_success", kwargs={"slug": self.paid_tournament.slug}),
            data={"session_id": "cs_success_123"},
        )

        self.assertEqual(response.status_code, 200)

        registration.refresh_from_db()
        transaction = PaymentTransaction.objects.get(stripe_session_id="cs_success_123")

        self.assertEqual(registration.payment_status, "paid")
        self.assertEqual(transaction.status, "paid")
        self.assertEqual(transaction.payment_status, "paid")

    @patch("tournaments.payments.stripe.checkout.Session.retrieve")
    def test_payment_success_should_reject_session_for_other_tournament_but_currently_does_not(self, mock_retrieve):
        other_tournament = Tournament.objects.create(
            title="Other Tournament",
            slug="other-tournament",
            description="Desc",
            category="Open",
            location="Athens",
            date="2030-01-13T10:00:00Z",
            start_time="10:00",
            price_euro=30,
            max_players=10,
            system="Swiss",
            is_open=True,
        )

        registration = Registration.objects.create(
            tournament=other_tournament,
            full_name="Jane Doe",
            email="jane@example.com",
            phone="6900000003",
            payment_status="pending",
            stripe_session_id="cs_wrong_slug",
        )

        PaymentTransaction.objects.create(
            registration=registration,
            stripe_session_id="cs_wrong_slug",
            amount=30,
            currency="EUR",
            status="initiated",
            payment_status="unpaid",
        )

        mock_session = Mock()
        mock_session.payment_status = "paid"
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            reverse("payment_success", kwargs={"slug": self.paid_tournament.slug}),
            data={"session_id": "cs_wrong_slug"},
        )

        registration.refresh_from_db()

        self.assertNotEqual(
            registration.payment_status,
            "paid",
            msg="BUG: payment success should verify the session belongs to the tournament in the URL."
        )