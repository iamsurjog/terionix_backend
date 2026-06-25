from django.db import models


class ContentSection(models.Model):
    section_key = models.CharField(max_length=64, unique=True)
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["section_key"]

    def __str__(self):
        return self.section_key


class ContactSubmission(models.Model):
    TYPE_CHOICES = [
        ("general", "General Inquiry"),
        ("career", "Career Application"),
        ("quote", "Quote Request"),
    ]

    submission_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    form_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_submission_type_display()}] {self.created_at.isoformat()}"


class LeaderboardEntry(models.Model):
    name = models.CharField(max_length=128)
    time = models.FloatField(help_text="Time in seconds (lower is better)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["time", "created_at"]
        verbose_name_plural = "leaderboard entries"

    def __str__(self):
        return f"{self.name} \u2013 {self.time}s"


class GameItem(models.Model):
    name = models.CharField(max_length=128)
    recyclable = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class EmailConfig(models.Model):
    to_email = models.EmailField(blank=True, default="", help_text="Default recipient email for daily digest")
    smtp_host = models.CharField(max_length=256, blank=True, default="")
    smtp_port = models.IntegerField(null=True, blank=True)
    smtp_user = models.CharField(max_length=256, blank=True, default="")
    smtp_password = models.CharField(max_length=512, blank=True, default="")
    use_tls = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "email config"
        verbose_name_plural = "email config"

    def __str__(self):
        return f"EmailConfig → {self.to_email}"


class Tender(models.Model):
    serial_no = models.CharField(max_length=64)
    published_date = models.CharField(max_length=32)
    closing_date = models.CharField(max_length=32)
    opening_date = models.CharField(max_length=32)
    title = models.TextField()
    reference_identifiers = models.JSONField(default=list)
    organization_chain = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "tenders"

    def __str__(self):
        return self.title
