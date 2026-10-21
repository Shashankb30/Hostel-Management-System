from django.core.management.base import BaseCommand, CommandError

from accounts import lockout
from core.models import UserAccount


class Command(BaseCommand):
    help = (
        'Unlock an account that was locked after repeated failed logins. '
        'Use this when the only administrator is locked out.'
    )

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']
        try:
            account = UserAccount.objects.select_related('user').get(user__username=username)
        except UserAccount.DoesNotExist:
            raise CommandError(f'No HMS account found for username {username!r}') from None
        lockout.unlock(account)
        self.stdout.write(self.style.SUCCESS(f'Account {username} is unlocked.'))
