import uuid

from django.db import migrations, models


def populate_verification_tokens(apps, schema_editor):
    Registration = apps.get_model("tournaments", "Registration")

    for registration in Registration.objects.filter(
        verification_token__isnull=True
    ).iterator():
        registration.verification_token = uuid.uuid4()
        registration.save(update_fields=["verification_token"])


class Migration(migrations.Migration):

    dependencies = [
        (
            "tournaments",
            "0007_registration_email_verified_and_more",
        ),
    ]

    operations = [
        # Give every existing registration its own UUID first
        migrations.RunPython(
            populate_verification_tokens,
            reverse_code=migrations.RunPython.noop,
        ),

        # Then make the field mandatory + unique
        migrations.AlterField(
            model_name="registration",
            name="verification_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]