from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from tournaments.payments import stripe_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tournaments/", include("tournaments.urls")),
    path("trainings/", include("trainings.urls")),
    path("accounts/", include("accounts.urls")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True
        ),
        name="login"
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="/tournaments/"),
        name="logout"
),

    # Stripe webhook
    path("webhook/stripe/", stripe_webhook, name="stripe_webhook"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)