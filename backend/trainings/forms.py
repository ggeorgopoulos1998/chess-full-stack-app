from django import forms
from .models import TrainingBooking


class TrainingBookingForm(forms.ModelForm):
    class Meta:
        model = TrainingBooking
        fields = ["full_name", "email", "phone", "notes"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Ονοματεπώνυμο"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Τηλέφωνο"}),
            "notes": forms.Textarea(attrs={"placeholder": "Σχόλια", "rows": 4}),
        }