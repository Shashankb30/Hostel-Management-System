"""NFR-04 / NFR.08: Database restore management command."""
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Restore the HMS database from a backup file (NFR-04).'

    def add_arguments(self, parser):
        parser.add_argument('backup_file', type=str, help='Path to the backup file (.json or .sqlite3)')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bypass confirmation prompt when restoring',
        )

    def handle(self, *args, **options):
        src_path = Path(options['backup_file'])
        if not src_path.is_absolute():
            src_path = (settings.BASE_DIR / src_path).resolve()

        if not src_path.exists():
            raise CommandError(f'Backup file does not exist: {src_path}')

        if src_path.suffix == '.sqlite3':
            db_config = settings.DATABASES['default']
            if 'sqlite' not in db_config['ENGINE']:
                raise CommandError('Cannot restore .sqlite3 backup onto a non-SQLite database.')
            dest_db = Path(db_config['NAME'])
            shutil.copy2(src_path, dest_db)
            self.stdout.write(self.style.SUCCESS(
                f'Binary database restored successfully from:\n  {src_path} -> {dest_db}'
            ))
            return

        if src_path.suffix == '.json':
            self.stdout.write(f'Restoring database from JSON fixture: {src_path}...')
            with transaction.atomic():
                call_command('loaddata', str(src_path))
            self.stdout.write(self.style.SUCCESS(
                f'Database records restored successfully from fixture:\n  {src_path}'
            ))
            return

        raise CommandError(f'Unsupported backup file extension: {src_path.suffix}. Expected .json or .sqlite3.')
