import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from api.models import ContentSection, GameItem, LeaderboardEntry

FALLBACK_PATHS = [
    settings.BASE_DIR.parent / "frontend" / "content.json",
    settings.BASE_DIR / "content.json",
    settings.BASE_DIR / "api" / "content.json",
]


class Command(BaseCommand):
    help = "Seed content from content.json into the database"

    def add_arguments(self, parser):
        parser.add_argument("--path", type=str, help="Path to content.json")

    def handle(self, *args, **options):
        if options.get("path"):
            path = Path(options["path"])
        else:
            path = None
            for p in FALLBACK_PATHS:
                if p.exists():
                    path = p
                    break
            if path is None:
                self.stderr.write(
                    "content.json not found. Provide --path or ensure one of: "
                    + "; ".join(str(p) for p in FALLBACK_PATHS)
                )
                return

        if not path.exists():
            self.stderr.write(f"content.json not found at {path}")
            return

        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)

        for key in [
            "site", "navbar", "home", "solutions", "innovation",
            "impactInsights", "about", "history", "careers", "contact",
            "learn", "social", "game",
        ]:
            if key in data:
                ContentSection.objects.update_or_create(
                    section_key=key, defaults={"data": data[key]}
                )
                self.stdout.write(f"  \u2713 content  {key}")

        if "leaderboard" in data:
            ContentSection.objects.update_or_create(
                section_key="leaderboard", defaults={"data": data["leaderboard"]}
            )
            self.stdout.write("  \u2713 content  leaderboard")

        GameItem.objects.all().delete()
        for item in data.get("game", {}).get("items", []):
            GameItem.objects.create(
                name=item["name"], recyclable=item["recyclable"]
            )
        self.stdout.write(f"  \u2713 game     {GameItem.objects.count()} items")

        LeaderboardEntry.objects.all().delete()
        for entry in data.get("leaderboard", []):
            LeaderboardEntry.objects.create(
                name=entry["name"], time=entry["time"]
            )
        self.stdout.write(
            f"  \u2713 leaderboard  {LeaderboardEntry.objects.count()} entries"
        )

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "", "admin")
            self.stdout.write("  \u2713 superuser admin / admin")
        else:
            self.stdout.write("  ~ superuser admin already exists")

        self.stdout.write(self.style.SUCCESS("Done seeding."))
