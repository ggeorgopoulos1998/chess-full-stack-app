
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta

from .models import Coach, TrainingSession, TrainingBooking


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    TOURNAMENT_ADMIN_EMAIL="admin@example.com",
)
class TrainingNotificationTests(TestCase):

    def setUp(self):
        self.coach = Coach.objects.create(
            first_name="Test",
            last_name="Coach",
            slug="test-coach",
            short_bio="Test coach",
        )

        self.session = TrainingSession.objects.create(
            coach=self.coach,
            title="Test Training",
            slug="test-training",
            description="Automated notification test",
            date=timezone.now() + timedelta(days=7),
            start_time="18:00",
            duration_minutes=60,
            session_type="group",
            max_participants=10,
            is_open=True,
        )

        self.url = reverse(
            "training_detail",
            args=[self.session.id],
        )

        self.registration_data = {
            "full_name": "Test Participant",
            "email": "test@example.com",
            "phone": "6900000000",
            "notes": "Automated test",
        }

    def test_successful_registration_sends_one_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.url,
                self.registration_data,
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("success=1", response.url)

        self.assertEqual(
            TrainingBooking.objects.filter(
                training_session=self.session
            ).count(),
            1,
        )

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.to, ["admin@example.com"])
        self.assertIn("Test Training", email.subject)
        self.assertIn("Test Participant", email.body)

    def test_duplicate_registration_sends_no_extra_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                self.url,
                self.registration_data,
            )

        self.assertEqual(len(mail.outbox), 1)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                self.url,
                self.registration_data,
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("duplicate=1", response.url)

        self.assertEqual(
            TrainingBooking.objects.filter(
                training_session=self.session
            ).count(),
            1,
        )

        self.assertEqual(len(mail.outbox), 1)
