from django import forms
from .models import Registration, TournamentPostponementRequest


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["full_name", "email", "phone", "club", "elo", "notes"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Ονοματεπώνυμο"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Τηλέφωνο"}),
            "club": forms.TextInput(attrs={"placeholder": "Σύλλογος (προαιρετικό)"}),
            "elo": forms.NumberInput(attrs={"placeholder": "ELO (προαιρετικό)"}),
            "notes": forms.Textarea(attrs={"placeholder": "Σχόλια", "rows": 4}),
        }


class TournamentPostponementRequestForm(forms.ModelForm):
    class Meta:
        model = TournamentPostponementRequest
        fields = ["requested_date", "reason"]
        widgets = {
            "requested_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"placeholder": "Αιτιολογία αναβολής", "rows": 4}),
        }