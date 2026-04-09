from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignUpForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("/tournaments/")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/tournaments/")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})