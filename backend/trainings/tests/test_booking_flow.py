from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from trainings.models import Coach, TrainingSession, TrainingBooking


class TrainingBookingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="traininguser",
            email="training@example.com",
            password="pass1234"
        )

        self.coach = Coach.objects.create(
            first_name="Magnus",
            last_name="Coach",
            slug="magnus-coach",
            short_bio="Elite coach",
            is_active=True,
        )

        self.open_session = TrainingSession.objects.create(
            coach=self.coach,
            title="Open Session",
            slug="open-session",
            description="Training desc",
            date="2030-02-01T10:00:00Z",
            start_time="10:00",
            duration_minutes=60,
            session_type="group",
            max_participants=2,
            price_euro=15,
            is_open=True,
        )

        self.closed_session = TrainingSession.objects.create(
            coach=self.coach,
            title="Closed Session",
            slug="closed-session",
            description="Training desc",
            date="2030-02-02T10:00:00Z",
            start_time="11:00",
            duration_minutes=60,
            session_type="group",
            max_participants=2,
            price_euro=15,
            is_open=False,
        )

        self.valid_post_data = {
            "full_name": "Student One",
            "email": "student@example.com",
            "phone": "6900000004",
            "notes": "Looking forward",
        }

    def test_open_training_allows_booking(self):
        response = self.client.post(
            reverse("training_detail", kwargs={"id": self.open_session.id}),
            data=self.valid_post_data,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            TrainingBooking.objects.filter(training_session=self.open_session).count(),
            1
        )

    def test_training_capacity_limit(self):
        TrainingBooking.objects.create(
            training_session=self.open_session,
            full_name="Student A",
            email="a@example.com",
            phone="6900000005",
        )
        TrainingBooking.objects.create(
            training_session=self.open_session,
            full_name="Student B",
            email="b@example.com",
            phone="6900000006",
        )

        response = self.client.post(
            reverse("training_detail", kwargs={"id": self.open_session.id}),
            data={
                "full_name": "Student C",
                "email": "c@example.com",
                "phone": "6900000007",
            },
        )

        self.assertEqual(
            TrainingBooking.objects.filter(training_session=self.open_session).count(),
            2
        )

    def test_closed_training_should_reject_direct_post_but_currently_does_not(self):
        response = self.client.post(
            reverse("training_detail", kwargs={"id": self.closed_session.id}),
            data=self.valid_post_data,
        )

        self.assertEqual(
            TrainingBooking.objects.filter(training_session=self.closed_session).count(),
            0,
            msg="BUG: closed trainings should not accept direct POST booking."
        )

    def test_same_user_should_not_book_same_training_twice_but_currently_can(self):
        self.client.login(username="traininguser", password="pass1234")

        self.client.post(
            reverse("training_detail", kwargs={"id": self.open_session.id}),
            data=self.valid_post_data,
        )
        self.client.post(
            reverse("training_detail", kwargs={"id": self.open_session.id}),
            data=self.valid_post_data,
        )

        self.assertEqual(
            TrainingBooking.objects.filter(
                training_session=self.open_session,
                user=self.user,
            ).count(),
            1,
            msg="BUG: same user should not be able to book the same training twice."
        )