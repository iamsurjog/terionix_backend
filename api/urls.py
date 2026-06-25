from django.urls import path
from rest_framework.routers import DefaultRouter

from . import tender_views, views

router = DefaultRouter(trailing_slash=False)
router.register(r"content", views.ContentSectionViewSet, basename="content")
router.register(r"submissions", views.ContactSubmissionViewSet, basename="submission")
router.register(r"leaderboard", views.LeaderboardEntryViewSet, basename="leaderboard")
router.register(r"game-items", views.GameItemViewSet, basename="game-item")
router.register(r"email-config", views.EmailConfigViewSet, basename="email-config")

urlpatterns = [
    # Tenders
    path("tenders", tender_views.TenderListView.as_view(), name="tender-list"),
    path("tenders/refresh", tender_views.refresh_tenders, name="tender-refresh"),
    path("tenders/scrape-status", tender_views.scrape_status, name="tender-scrape-status"),
    path("scraper/callback", tender_views.scraper_callback, name="scraper-callback"),
    # Health
    path("checkhealth", views.checkhealth, name="checkhealth"),
    # Content
    path("content", views.content_tree, name="content-tree"),
    path("content/<str:section_key>", views.content_detail, name="content-detail"),
    # Contact forms
    path(
        "contact/<str:submission_type>",
        views.submit_contact,
        name="submit-contact",
    ),
    # Auth
    path("auth/login", views.login_view, name="api-login"),
    path("auth/logout", views.logout_view, name="api-logout"),
    path("auth/session", views.session_view, name="api-session"),
    path("auth/change-password", views.change_password_view, name="api-change-password"),
]

urlpatterns += router.urls
