from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)
router.register(r"content", views.ContentSectionViewSet, basename="content")
router.register(r"submissions", views.ContactSubmissionViewSet, basename="submission")
router.register(r"leaderboard", views.LeaderboardEntryViewSet, basename="leaderboard")
router.register(r"game-items", views.GameItemViewSet, basename="game-item")

urlpatterns = [
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
