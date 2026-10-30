from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.seed import USERS, seed


class Command(BaseCommand):
    help = (
        'Load the repeatable Test Plan seed data (users, students, rooms, one fee). '
        'Safe to run many times: it resets the seeded records to their baseline.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Allow seeding when DEBUG is off. Never use this on a production database.',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['force']:
            raise CommandError(
                'Refusing to load test credentials while DEBUG is off. '
                'Use --force only on a throw-away database.'
            )
        counts = seed()
        self.stdout.write(self.style.SUCCESS(
            f"Seed data ready ({counts['created']} created, {counts['updated']} updated)."
        ))
        self.stdout.write('Test accounts (username / password / role):')
        for username, password, role, *_ in USERS:
            self.stdout.write(f'  {username:<8} {password:<10} {role}')
