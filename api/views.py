from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import ContentSection, ContactSubmission, LeaderboardEntry, GameItem
from .serializers import (
    ContentSectionSerializer,
    ContactSubmissionSerializer,
    LeaderboardEntrySerializer,
    GameItemSerializer,
)


class ContentSectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentSection.objects.all()
    serializer_class = ContentSectionSerializer
    lookup_field = "section_key"


@api_view(["GET"])
def content_tree(request):
    sections = ContentSection.objects.all()
    tree = {s.section_key: s.data for s in sections}
    return Response(tree)


@api_view(["GET", "PATCH"])
def content_detail(request, section_key):
    try:
        section = ContentSection.objects.get(section_key=section_key)
    except ContentSection.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ContentSectionSerializer(section).data)

    # PATCH — requires authentication
    if not request.user.is_authenticated:
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    data = request.data.get("data")
    if data is not None:
        section.data = data
        section.save()
    return Response({"success": True})


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def submit_contact(request, submission_type):
    if submission_type not in dict(ContactSubmission.TYPE_CHOICES):
        return Response(
            {"error": f"Invalid type '{submission_type}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = ContactSubmissionSerializer(
        data={"submission_type": submission_type, "form_data": request.data}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class ContactSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [IsAuthenticated]


class LeaderboardEntryViewSet(viewsets.ModelViewSet):
    queryset = LeaderboardEntry.objects.all()
    serializer_class = LeaderboardEntrySerializer

    def get_permissions(self):
        if self.request.method in ("GET", "POST"):
            return [AllowAny()]
        return [IsAuthenticated()]


class GameItemViewSet(viewsets.ModelViewSet):
    queryset = GameItem.objects.all()
    serializer_class = GameItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(username=username, password=password)
    if user is not None:
        from django.contrib.auth import login as django_login
        from django.middleware.csrf import get_token

        django_login(request, user)
        return Response({
            "success": True,
            "user": user.username,
            "csrfToken": get_token(request),
        })
    return Response(
        {"success": False, "error": "Invalid credentials"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


@api_view(["POST"])
def logout_view(request):
    from django.contrib.auth import logout as django_logout
    django_logout(request)
    return Response({"success": True})


@api_view(["GET"])
def session_view(request):
    return Response({
        "authenticated": request.user.is_authenticated,
        "user": request.user.username if request.user.is_authenticated else None,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    current = request.data.get("current_password", "")
    new = request.data.get("new_password", "")

    if not request.user.check_password(current):
        return Response(
            {"success": False, "error": "Current password is incorrect"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(new) < 4:
        return Response(
            {"success": False, "error": "New password must be at least 4 characters"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(new)
    request.user.save()
    return Response({"success": True})
