from django.core.management.base import BaseCommand, CommandError

from apps.movies.showcase import SHOWCASE_SECTION_LIMIT, refresh_catalog_showcase


class Command(BaseCommand):
    help = (
        "Refresh cached catalog showcase from TMDb, import titles into the local "
        "database, and compare weekly top positions with the previous refresh."
    )

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Refresh even if today's cache is already up to date.")
        parser.add_argument(
            "--top-limit",
            type=int,
            default=SHOWCASE_SECTION_LIMIT,
            help="How many titles to keep in each weekly top section.",
        )
        parser.add_argument(
            "--genre-limit",
            type=int,
            default=SHOWCASE_SECTION_LIMIT,
            help="How many titles to keep in each genre shelf.",
        )

    def handle(self, *args, **options):
        try:
            result = refresh_catalog_showcase(
                force=options["force"],
                top_limit=options["top_limit"],
                genre_limit=options["genre_limit"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        summary = result.get("summary", {})
        if not result.get("refreshed"):
            self.stdout.write(self.style.WARNING("Showcase is already fresh for today."))
            return

        self.stdout.write(self.style.SUCCESS("Showcase cache refreshed successfully."))
        self.stdout.write(f"Imported or updated titles: {summary.get('total_movies', 0)}")
        for slug, section_info in summary.get("sections", {}).items():
            self.stdout.write(
                f"- {slug}: {section_info['count']} items, "
                f"new={section_info['new']}, up={section_info['up']}, down={section_info['down']}"
            )
