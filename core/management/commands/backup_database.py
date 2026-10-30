"""NFR-04 / NFR.08: Database backup management command."""
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create a consistent snapshot/backup of the HMS database (NFR-04).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Target path for the backup file (defaults to backups/hms_backup_<timestamp>.json)',
        )
        parser.add_argument(
            '--sqlite-raw',
            action='store_true',
            help='Take a binary snapshot of the SQLite database file directly (SQLite only)',
        )

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backups_dir = settings.BASE_DIR / 'backups'
        backups_dir.mkdir(parents=True, exist_ok=True)

        if options['sqlite_raw']:
            db_config = settings.DATABASES['default']
            if 'sqlite' not in db_config['ENGINE']:
                raise CommandError('--sqlite-raw can only be used with SQLite databases.')
            src_db = Path(db_config['NAME'])
            if not src_db.exists():
                raise CommandError(f'Source database file not found at: {src_db}')
            dest = Path(options['output']) if options['output'] else backups_dir / f'hms_backup_{timestamp}.sqlite3'
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_db, dest)
            size_kb = dest.stat().st_size / 1024
            self.stdout.write(self.style.SUCCESS(
                f'Binary database backup created successfully:\n  File: {dest}\n  Size: {size_kb:.1f} KB'
            ))
            return str(dest)

        dest = Path(options['output']) if options['output'] else backups_dir / f'hms_backup_{timestamp}.json'
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Dump all HMS models in dependency order
        target_apps = [
            'auth.user',
            'core',
            'accounts',
            'students',
            'rooms',
            'allocation',
            'attendance',
            'complaints',
            'fees',
            'visitors',
            'leave',
            'notices',
        ]
        with open(dest, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                *target_apps,
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=f,
            )

        size_kb = dest.stat().st_size / 1024
        self.stdout.write(self.style.SUCCESS(
            f'JSON database backup created successfully:\n  File: {dest}\n  Size: {size_kb:.1f} KB'
        ))
        return str(dest)
