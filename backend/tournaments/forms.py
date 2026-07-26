from django import forms
from .models import Registration, TournamentPostponementRequest


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration

        fields = [
            "full_name",
            "email",
            "phone",
            "birth_date",
            "fide_id",
            "club",
            "elo",
            "notes",
        ]

        labels = {
            "full_name": "Ονοματεπώνυμο",
            "email": "Email",
            "phone": "Τηλέφωνο",
            "birth_date": "Ημερομηνία γέννησης",
            "fide_id": "FIDE ID",
            "club": "Σύλλογος",
            "elo": "ELO",
            "notes": "Σχόλια",
        }

        widgets = {
            "full_name": forms.TextInput(
                attrs={"placeholder": "Ονοματεπώνυμο"}
            ),
            "email": forms.EmailInput(
                attrs={"placeholder": "Email"}
            ),
            "phone": forms.TextInput(
                attrs={"placeholder": "Τηλέφωνο"}
            ),
            "birth_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "fide_id": forms.TextInput(
                attrs={
                    "placeholder": "FIDE ID (προαιρετικό)",
                    "inputmode": "numeric",
                }
            ),
            "club": forms.TextInput(
                attrs={"placeholder": "Σύλλογος (προαιρετικό)"}
            ),
            "elo": forms.NumberInput(
                attrs={"placeholder": "ELO (προαιρετικό)"}
            ),
            "notes": forms.Textarea(
                attrs={"placeholder": "Σχόλια", "rows": 4}
            ),
        }


class TournamentPostponementRequestForm(forms.ModelForm):
    class Meta:
        model = TournamentPostponementRequest
        fields = ["requested_date", "reason"]
        widgets = {
            "requested_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"placeholder": "Αιτιολογία αναβολής", "rows": 4}),
        }