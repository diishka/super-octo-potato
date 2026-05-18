from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections

from apps.accounts.models import User
from apps.feed.models import Activity, ActivityComment, ActivityLike
from apps.movies.models import Genre, LinkVote, Movie, MovieLink, UserMovie
from apps.social.models import Follow


LEGACY_ALIAS = "legacy_sqlite"
IMPORT_MODELS = [
    User,
    Genre,
    Movie,
    Movie.genres.through,
    UserMovie,
    Follow,
    MovieLink,
    LinkVote,
    Activity,
    ActivityLike,
    ActivityComment,
]


class Command(BaseCommand):
    help = "Import application data from a legacy SQLite database into the configured PostgreSQL database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=str(Path(settings.BASE_DIR) / "db.sqlite3"),
            help="Path to the legacy SQLite database file.",
        )
        parser.add_argument(
            "--skip-migrate",
            action="store_true",
            help="Skip running migrations on the PostgreSQL database before import.",
        )
        parser.add_argument(
            "--flush-target",
            action="store_true",
            help="Explicitly flush the target PostgreSQL database before import.",
        )

    def handle(self, *args, **options):
        source_path = Path(options["source"]).expanduser().resolve()
        if not source_path.exists():
            raise CommandError(f"Legacy SQLite database not found: {source_path}")

        self._register_legacy_database(source_path)

        try:
            connections[LEGACY_ALIAS].ensure_connection()
            self._validate_source_database()

            if not options["skip_migrate"]:
                self.stdout.write("Applying migrations on PostgreSQL...")
                call_command("migrate", database=DEFAULT_DB_ALIAS, interactive=False, verbosity=options["verbosity"])

            if self._target_has_existing_data():
                if not options["flush_target"]:
                    raise CommandError(
                        "Target PostgreSQL database already contains application data. "
                        "Re-run with --flush-target if you really want to replace it."
                    )
                self.stdout.write("Flushing PostgreSQL database before import...")
                call_command("flush", database=DEFAULT_DB_ALIAS, interactive=False, verbosity=0)

            totals = {}
            for model in IMPORT_MODELS:
                copied = self._copy_model(model)
                totals[model._meta.label] = copied
                self.stdout.write(f"Imported {copied} rows into {model._meta.label}")

            self._reset_sequences(IMPORT_MODELS)
        finally:
            self._close_legacy_database()

        summary = ", ".join(f"{label}: {count}" for label, count in totals.items())
        self.stdout.write(self.style.SUCCESS(f"Legacy SQLite import complete. {summary}"))

    def _register_legacy_database(self, source_path: Path) -> None:
        connections.databases[LEGACY_ALIAS] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(source_path),
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_HEALTH_CHECKS": False,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {},
            "TIME_ZONE": None,
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
            "TEST": {},
        }

    def _close_legacy_database(self) -> None:
        if LEGACY_ALIAS in connections:
            connections[LEGACY_ALIAS].close()
        connections.databases.pop(LEGACY_ALIAS, None)

    def _validate_source_database(self) -> None:
        required_tables = {"accounts_user", "movies_movie", "movies_usermovie"}
        with connections[LEGACY_ALIAS].cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
        missing = sorted(required_tables - tables)
        if missing:
            raise CommandError(
                f"Legacy SQLite database is missing required tables: {', '.join(missing)}"
            )

    def _copy_model(self, model, batch_size: int = 500) -> int:
        fields = [field for field in model._meta.local_fields]
        source_qs = model._default_manager.using(LEGACY_ALIAS).all().order_by(model._meta.pk.attname)
        buffer = []
        total = 0

        for source_obj in source_qs.iterator(chunk_size=batch_size):
            payload = {field.attname: getattr(source_obj, field.attname) for field in fields}
            buffer.append(model(**payload))

            if len(buffer) >= batch_size:
                model._default_manager.using(DEFAULT_DB_ALIAS).bulk_create(buffer, batch_size=batch_size)
                total += len(buffer)
                buffer.clear()

        if buffer:
            model._default_manager.using(DEFAULT_DB_ALIAS).bulk_create(buffer, batch_size=batch_size)
            total += len(buffer)

        return total

    def _target_has_existing_data(self) -> bool:
        return any(
            model._default_manager.using(DEFAULT_DB_ALIAS).exists()
            for model in (User, Movie, UserMovie, Activity, Follow)
        )

    def _reset_sequences(self, models) -> None:
        connection = connections[DEFAULT_DB_ALIAS]
        sql_statements = connection.ops.sequence_reset_sql(no_style(), models)
        if not sql_statements:
            return

        with connection.cursor() as cursor:
            for statement in sql_statements:
                cursor.execute(statement)
