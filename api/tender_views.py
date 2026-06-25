import os
import uuid

import httpx
from django.db import models, transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Tender


class TenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = [
            "id",
            "serial_no",
            "published_date",
            "closing_date",
            "opening_date",
            "title",
            "reference_identifiers",
            "organization_chain",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TenderListView(generics.ListAPIView):
    queryset = Tender.objects.all()
    serializer_class = TenderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                models.Q(title__icontains=q)
                | models.Q(organization_chain__icontains=q)
                | models.Q(reference_identifiers__icontains=q)
            )
        return qs


def _get_scraper_url() -> str:
    return os.environ.get("SCRAPER_API_URL", "http://localhost:8002")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refresh_tenders(request):
    scraper_url = f"{_get_scraper_url()}/scrape"
    job_id = str(uuid.uuid4())

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                scraper_url,
                headers={"X-Job-Id": job_id},
            )

            if resp.status_code == 409:
                return Response(resp.json(), status=status.HTTP_409_CONFLICT)

            resp.raise_for_status()
    except httpx.RequestError:
        return Response(
            {"error": "Scraper is unreachable"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"job_id": job_id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def scrape_status(request):
    job_id = request.query_params.get("job_id", "")
    if not job_id:
        return Response(
            {"error": "job_id query parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{_get_scraper_url()}/status",
                params={"job_id": job_id},
            )
            data = resp.json()
    except httpx.RequestError:
        return Response(
            {"status": "error", "detail": "Scraper unavailable"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"job_id": job_id, "status": data.get("status", "unknown")})


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def scraper_callback(request):
    tenders = request.data.get("tenders", [])

    if not isinstance(tenders, list) or len(tenders) == 0:
        return Response(
            {"error": "tenders must be a non-empty list"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tender_objs = [
        Tender(
            serial_no=t.get("serial_no", ""),
            published_date=t.get("published_date", ""),
            closing_date=t.get("closing_date", ""),
            opening_date=t.get("opening_date", ""),
            title=t.get("title", ""),
            reference_identifiers=t.get("reference_identifiers", []),
            organization_chain=t.get("organization_chain", ""),
        )
        for t in tenders
    ]

    with transaction.atomic():
        Tender.objects.all().delete()
        Tender.objects.bulk_create(tender_objs)

    return Response({"success": True, "count": len(tender_objs)})
