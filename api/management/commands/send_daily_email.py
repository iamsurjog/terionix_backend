"""
Management command to send a daily email digest of contact submissions.
Designed to be run via cron at 6am:

    0 6 * * * cd /path/to/backend && python manage.py send_daily_email
"""

import datetime
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import ContactSubmission, EmailConfig


class Command(BaseCommand):
    help = "Send daily email digest of contact submissions (run at 6am via cron)"

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        hour = now.hour
        minute = now.minute

        # Allow running within 5 minutes of 6am
        if not (hour == 6 and minute <= 5) and not (hour == 5 and minute >= 55):
            self.stdout.write(
                self.style.WARNING(
                    f"Current time {now:%H:%M} is not within 5min of 06:00 — skipping"
                )
            )
            return

        cfg = EmailConfig.objects.first()
        if cfg is None:
            self.stdout.write(self.style.ERROR("No EmailConfig found — skipping"))
            return

        since = now - timedelta(hours=24)
        submissions = ContactSubmission.objects.filter(created_at__gte=since).order_by(
            "-created_at"
        )

        count = submissions.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No submissions in the last 24h — nothing to send"))
            return

        # Build HTML table
        rows_html = ""
        for s in submissions:
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
            f"<html><body>"
            f"<h2>Daily Contact Submissions Digest</h2>"
            f"<p>{count} submission(s) in the last 24 hours</p>"
            f"<table style='border-collapse:collapse;width:100%'>{rows_html}</table>"
            f"<p><small>Automatically sent from Terionix backend</small></p>"
            f"</body></html>"
        )

        subject = f"Contact Submissions Digest — {now.strftime('%Y-%m-%d')}"

        try:
            send_mail(
                subject=subject,
                message="",
                html_message=html,
                from_email=None,
                recipient_list=[cfg.to_email],
                fail_silently=False,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent digest with {count} submission(s) to {cfg.to_email}"
            )
        )
