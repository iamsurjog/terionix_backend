import csv
import io
import json

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import ContentSection, ContactSubmission, EmailConfig, LeaderboardEntry, GameItem
from .serializers import (
    ContactSubmissionSerializer,
    ContentSectionSerializer,
    EmailConfigSerializer,
    GameItemSerializer,
    LeaderboardEntrySerializer,
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


class SubmissionPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class ContactSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SubmissionPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["submission_type"]
    ordering_fields = ["created_at", "submission_type", "id"]
    ordering = ["-created_at"]

    def _get_filtered_queryset(self):
        """Apply filters + ordering from request query params, return queryset."""
        qs = self.filter_queryset(self.get_queryset())
        return qs

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        qs = self._get_filtered_queryset()

        # Collect all form_data keys for CSV columns
        rows = list(qs.values("id", "submission_type", "created_at", "form_data"))
        all_keys = []
        for r in rows:
            if isinstance(r["form_data"], dict):
                for k in r["form_data"]:
                    if k not in all_keys:
                        all_keys.append(k)

        def stream():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            header = ["id", "submission_type", "created_at"] + all_keys
            writer.writerow(header)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            for r in rows:
                row = [r["id"], r["submission_type"], r["created_at"].isoformat() if r["created_at"] else ""]
                fd = r["form_data"] if isinstance(r["form_data"], dict) else {}
                row += [fd.get(k, "") for k in all_keys]
                writer.writerow(row)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            stream(), content_type="text/csv"
        )
        response["Content-Disposition"] = 'attachment; filename="submissions.csv"'
        return response

    @action(detail=False, methods=["get"], url_path="export/json")
    def export_json(self, request):
        qs = self._get_filtered_queryset()
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        response = Response(data)
        response["Content-Disposition"] = 'attachment; filename="submissions.json"'
        return response

    @action(detail=False, methods=["post"], url_path="send-email")
    def send_email(self, request):
        to_email = request.data.get("to_email", "")
        subject = request.data.get("subject", "Contact Form Submissions")
        submission_ids = request.data.get("submission_ids", None)

        # If no to_email, try EmailConfig
        if not to_email:
            cfg = EmailConfig.objects.first()
            if cfg is None:
                return Response(
                    {"success": False, "error": "No EmailConfig found and no to_email provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            to_email = cfg.to_email

        # Fetch submissions
        if submission_ids and len(submission_ids) > 0:
            qs = ContactSubmission.objects.filter(id__in=submission_ids).order_by("-created_at")
        else:
            qs = ContactSubmission.objects.all().order_by("-created_at")

        if not qs.exists():
            return Response(
                {"success": False, "error": "No submissions to send"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build HTML table
        rows_html = ""
        for s in qs:
            fd = s.form_data if isinstance(s.form_data, dict) else {}
            fields_html = "".join(
                f"<tr><td style='padding:2px 8px;border:1px solid #ccc'>{k}</td>"
                f"<td style='padding:2px 8px;border:1px solid #ccc'>{v}</td></tr>"
                for k, v in fd.items()
            )
            rows_html += (
                f"<tr style='background:#f5f5f5'><td colspan='2' style='padding:4px 8px;font-weight:bold'>"
                f"[{s.get_submission_type_display()}] {s.created_at.isoformat()}</td></tr>"
                + fields_html
            )

        html = (
            f"<html><body><h2>{subject}</h2>"
            f"<table style='border-collapse:collapse;width:100%'>{rows_html}</table>"
            f"<p><small>Sent from Terionix backend</small></p></body></html>"
        )

        try:
            send_mail(
                subject=subject,
                message="",
                html_message=html,
                from_email=None,
                recipient_list=[to_email],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"success": True, "sent_to": to_email, "count": qs.count()})


class EmailConfigViewSet(viewsets.ModelViewSet):
    queryset = EmailConfig.objects.all()
    serializer_class = EmailConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the singleton config (first/only instance)."""
        obj = EmailConfig.objects.first()
        if obj is None:
            obj = EmailConfig.objects.create()
        return obj

    def list(self, request, *args, **kwargs):
        """GET → return the singleton config."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """POST → update the singleton config (upsert)."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save()


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
